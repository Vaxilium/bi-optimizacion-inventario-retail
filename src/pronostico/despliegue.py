"""Pronosticos de despliegue por SKU usando el modelo elegido por segmento."""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from src.pronostico.censura import corregir_historia
from src.pronostico.modelos import pronosticar
from src.pronostico.series import clasificar_xyz, clases_abc


def generar_despliegue(
    con: duckdb.DuckDBPyConnection,
    parametros: dict,
    seleccion: pd.DataFrame,
    mejor_global: str,
    factor_censura: float = 1.0,
) -> tuple[pd.DataFrame, dict]:
    """Genera 28 dias de pronostico para cada SKU con el modelo de su segmento ABC-XYZ."""
    config = parametros["pronostico"]
    horizonte = config["horizonte_dias"]
    ventana = config["ventana_entrenamiento_dias"]
    ventas = con.execute(
        """
        SELECT
            fecha,
            producto_id,
            SUM(venta_unidades) AS unidades,
            AVG(CASE WHEN en_promocion THEN 1.0 ELSE 0.0 END) AS promocion,
            AVG(CASE WHEN indicador_quiebre THEN 1.0 ELSE 0.0 END) AS quiebre
        FROM nucleo_hechos_ventas
        GROUP BY 1, 2
        """
    ).fetchdf()
    fechas = pd.date_range(ventas["fecha"].min(), ventas["fecha"].max(), freq="D")
    unidades = ventas.pivot_table(
        index="fecha", columns="producto_id", values="unidades", fill_value=0
    ).reindex(fechas, fill_value=0)
    promociones = ventas.pivot_table(
        index="fecha", columns="producto_id", values="promocion", fill_value=0
    ).reindex(fechas, fill_value=0)
    quiebres_sku = ventas.pivot_table(
        index="fecha", columns="producto_id", values="quiebre", fill_value=0
    ).reindex(fechas, fill_value=0)
    clases = clases_abc(con).set_index("producto_id")["clase_abc"].to_dict()
    modelos = dict(zip(seleccion["segmento"], seleccion["modelo"]))
    futuras = pd.date_range(fechas[-1] + pd.Timedelta(days=1), periods=horizonte, freq="D")
    filas = []
    usados: dict[str, int] = {}
    for producto_id in unidades.columns:
        valores = unidades[producto_id].to_numpy(dtype=float)
        abc = clases.get(producto_id, "C")
        xyz = clasificar_xyz(valores)
        segmento = f"{abc}-{xyz}"
        modelo = modelos.get(segmento, mejor_global)
        usados[modelo] = usados.get(modelo, 0) + 1
        historia = valores[-ventana:]
        quiebres = quiebres_sku[producto_id].to_numpy(dtype=float)[-ventana:]
        ajuste = 1.0
        if modelo.endswith("_sin_censura"):
            historia = corregir_historia(historia, quiebres, cuantil=config["cuantil_censura"])
        elif modelo.endswith("_ajustada"):
            ajuste = factor_censura
        promo_historia = promociones[producto_id].to_numpy(dtype=float)[-ventana:]
        yhat = pronosticar(
            modelo.replace("_sin_censura", "").replace("_ajustada", ""),
            historia, promo_historia, futuras, np.zeros(len(futuras)), config,
        ) * ajuste
        for fecha, valor in zip(futuras, yhat):
            filas.append(
                {
                    "producto_id": producto_id,
                    "fecha": fecha,
                    "pronostico_unidades": round(float(valor), 2),
                    "modelo": modelo,
                    "clase_abc": abc,
                    "clase_xyz": xyz,
                    "segmento": segmento,
                    "media_28d": round(float(historia[-28:].mean()), 2),
                }
            )
    resumen = {
        "filas": len(filas),
        "productos": int(unidades.shape[1]),
        "fecha_inicio": futuras[0].strftime("%Y-%m-%d"),
        "fecha_fin": futuras[-1].strftime("%Y-%m-%d"),
        "modelos_usados": usados,
    }
    return pd.DataFrame(filas), resumen
