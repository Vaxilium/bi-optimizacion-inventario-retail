"""Backtesting rolling-origin y generacion de pronosticos de despliegue.

Uso:
    python -m src.pronostico.ejecutar [--rapido]

Salidas:
    resultados/pronostico.json
    resultados/tablas/pronostico_*.csv
    resultados/pronosticos.parquet (ignorado por git)
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import duckdb
import pandas as pd

from src.comun.config import RUTA_ALMACEN, RUTA_RESULTADOS, asegurar_directorios, cargar_parametros
from src.comun.parquet import guardar_parquet
from src.comun.resultados import guardar_json, guardar_tabla
from src.pronostico.backtest import ejecutar_backtest
from src.pronostico.censura import cargar_verdad
from src.pronostico.despliegue import generar_despliegue
from src.pronostico.evaluacion import agregar, seleccionar_por_segmento
from src.pronostico.series import cargar_ventas, construir_series, estadisticas_pares, muestrear


def ejecutar(modo_rapido: bool = False) -> dict[str, Any]:
    inicio = time.time()
    parametros = cargar_parametros(modo_rapido)
    asegurar_directorios()
    config = parametros["pronostico"]
    con = duckdb.connect(str(RUTA_ALMACEN), read_only=True)
    try:
        print("[1/4] Preparando muestra estratificada de series sucursal-SKU...")
        ventas = cargar_ventas(con)
        pares = estadisticas_pares(con)
        muestra = muestrear(pares, config["n_sku_muestra"], parametros["proyecto"]["semilla"])
        series = construir_series(ventas, muestra, ("sucursal_id", "producto_id"))
        verdad = cargar_verdad(con, [s.identificador for s in series])
        guardar_tabla("pronostico_muestra", muestra[["sucursal_id", "producto_id", "clase_abc", "clase_xyz"]])
        print(f"      {len(series)} series; {muestra['clase_abc'].value_counts().to_dict()} por clase ABC")
        factor = _factor_censura(con)
        print(f"      factor de ajuste por censura: {factor:.4f} (1/tasa de llenado)")
        print("[2/4] Backtesting rolling-origin contra demanda potencial...")
        registros, predicciones, fechas_ultimo = ejecutar_backtest(
            series, verdad, parametros, factor
        )
        tabla_modelos = agregar(registros)
        seleccion = seleccionar_por_segmento(registros)
        mejor_global = str(tabla_modelos.iloc[0]["modelo"])
        print(f"      mejor modelo global: {mejor_global} "
              f"(WAPE {tabla_modelos.iloc[0]['wape']:.2%})")
        print("[3/4] Pronosticos de despliegue por SKU...")
        despliegue, resumen_despliegue = generar_despliegue(
            con, parametros, seleccion, mejor_global, factor
        )
        guardar_parquet(despliegue, RUTA_RESULTADOS / "pronosticos.parquet")
        print("[4/4] Guardando metricas y tablas...")
        ejemplo = _tabla_ejemplo(series, predicciones, fechas_ultimo, seleccion, mejor_global)
        por_clase = _por_clase(registros)
        guardar_tabla("pronostico_metricas_series", registros)
        guardar_tabla("pronostico_modelos", tabla_modelos)
        guardar_tabla("pronostico_seleccion", seleccion)
        guardar_tabla("pronostico_por_clase", por_clase)
        guardar_tabla("pronostico_ejemplo", ejemplo)
        guardar_tabla("pronostico_despliegue", despliegue.head(1000))
        salida = _resumen(
            parametros, registros, tabla_modelos, seleccion, por_clase,
            despliegue, resumen_despliegue, series, mejor_global, factor, inicio,
        )
        guardar_json("pronostico", salida)
        _imprimir(salida)
        return salida
    finally:
        con.close()


def _factor_censura(con: duckdb.DuckDBPyConnection) -> float:
    """Estima la demanda no capturada a partir de la tasa de llenado agregada."""
    fila = con.execute(
        """
        SELECT 1 - SUM(unidades_perdidas_estimadas)
                   / NULLIF(SUM(unidades) + SUM(unidades_perdidas_estimadas), 0)
        FROM mart_kpi_mensual
        """
    ).fetchone()
    tasa = float(fila[0]) if fila[0] else 1.0
    return 1 / tasa if tasa > 0 else 1.0


def _por_clase(registros: pd.DataFrame) -> pd.DataFrame:
    agrupado = (
        registros.groupby(["clase_abc", "modelo"])
        .agg(
            error_abs=("error_abs", "sum"),
            error_abs_semanal=("error_abs_semanal", "sum"),
            unidades_semanal=("unidades_semanal", "sum"),
            unidades=("unidades", "sum"),
        )
        .reset_index()
    )
    agrupado["wape"] = agrupado["error_abs"] / agrupado["unidades"].clip(lower=1e-9)
    agrupado["wape_semanal"] = agrupado["error_abs_semanal"] / agrupado[
        "unidades_semanal"
    ].clip(lower=1e-9)
    return agrupado.drop(columns=["error_abs", "unidades", "error_abs_semanal", "unidades_semanal"]).sort_values(["clase_abc", "wape_semanal"])


def _tabla_ejemplo(
    series, predicciones, fechas, seleccion, mejor_global
) -> pd.DataFrame:
    modelos = dict(zip(seleccion["segmento"], seleccion["modelo"]))
    candidatas = sorted(
        [s for s in series if s.clase_abc == "A"],
        key=lambda s: s.unidades[-28:].sum(), reverse=True,
    )[:3]
    filas = []
    for serie in candidatas:
        modelo = modelos.get(serie.segmento, mejor_global)
        for i, fecha in enumerate(fechas):
            filas.append(
                {
                    "serie": serie.identificador,
                    "fecha": fecha,
                    "real": serie.unidades[-28:][i],
                    "pronostico_actual": predicciones[(serie.identificador, "media_movil_28")][i],
                    "pronostico_mejor": predicciones[(serie.identificador, modelo)][i],
                    "modelo_mejor": modelo,
                }
            )
    return pd.DataFrame(filas)


def _resumen(
    parametros, registros, tabla_modelos, seleccion, por_clase, despliegue,
    resumen_despliegue, series, mejor_global, factor, inicio,
) -> dict[str, Any]:
    actual = tabla_modelos.set_index("modelo").loc["media_movil_28"]
    mejor = tabla_modelos.set_index("modelo").loc[mejor_global]
    total = (
        registros.groupby(["identificador", "modelo"])["error_abs_semanal"].sum().unstack()
    )
    victorias = total.idxmin(axis=1).value_counts().to_dict()
    mejoras = {
        modelo: 1 - fila["wape"] / actual["wape"]
        for modelo, fila in tabla_modelos.set_index("modelo").iterrows()
        if actual["wape"] > 0
    }
    mejoras_semanales = {
        modelo: 1 - fila["wape_semanal"] / actual["wape_semanal"]
        for modelo, fila in tabla_modelos.set_index("modelo").iterrows()
        if actual["wape_semanal"] > 0
    }
    return {
        "resumen": {
            "series_muestra": len(series),
            "origenes": parametros["pronostico"]["origenes"],
            "horizonte_dias": parametros["pronostico"]["horizonte_dias"],
            "ventana_entrenamiento_dias": parametros["pronostico"]["ventana_entrenamiento_dias"],
            "wape_actual": float(actual["wape"]),
            "wape_mejor": float(mejor["wape"]),
            "mejora_vs_actual": float(1 - mejor["wape"] / actual["wape"]),
            "wape_semanal_actual": float(actual["wape_semanal"]),
            "wape_semanal_mejor": float(mejor["wape_semanal"]),
            "mejora_semanal_vs_actual": float(
                1 - mejor["wape_semanal"] / actual["wape_semanal"]
            ),
            "mejor_modelo": mejor_global,
            "factor_censura": float(factor),
            "mae_actual": float(actual["mae_medio"]),
            "mae_mejor": float(mejor["mae_medio"]),
            "sesgo_actual": float(actual["sesgo"]),
            "sesgo_mejor": float(mejor["sesgo"]),
            "sesgo_semanal_actual": float(actual["sesgo_semanal"]),
            "sesgo_semanal_mejor": float(mejor["sesgo_semanal"]),
            "victorias": {k: int(v) for k, v in victorias.items()},
            "mejora_por_modelo": {k: float(v) for k, v in mejoras.items()},
            "mejora_semanal_por_modelo": {
                k: float(v) for k, v in mejoras_semanales.items()
            },
        },
        "modelos": _registros(tabla_modelos),
        "seleccion": _registros(seleccion),
        "por_clase_abc": _registros(por_clase),
        "despliegue": resumen_despliegue,
        "segundos": round(time.time() - inicio, 1),
    }


def _registros(tabla: pd.DataFrame) -> list[dict[str, Any]]:
    salida = []
    for fila in tabla.to_dict(orient="records"):
        limpio = {}
        for clave, valor in fila.items():
            if isinstance(valor, float) and pd.isna(valor):
                limpio[clave] = None
            elif hasattr(valor, "item"):
                limpio[clave] = valor.item()
            else:
                limpio[clave] = valor
        salida.append(limpio)
    return salida


def _imprimir(salida: dict[str, Any]) -> None:
    r = salida["resumen"]
    print(
        f"      WAPE diario {r['wape_actual']:.2%} -> {r['wape_mejor']:.2%}; "
        f"WAPE semanal {r['wape_semanal_actual']:.2%} -> {r['wape_semanal_mejor']:.2%} "
        f"({r['mejora_semanal_vs_actual']:.1%} de mejora) con {r['mejor_modelo']}; "
        f"{salida['despliegue']['filas']:,} pronosticos en "
        f"{salida['despliegue']['fecha_inicio']} a {salida['despliegue']['fecha_fin']}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
