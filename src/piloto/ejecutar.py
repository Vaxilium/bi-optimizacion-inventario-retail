"""Diseno y evaluacion del piloto controlado de 12 semanas.

Uso:
    python -m src.piloto.ejecutar

Salidas:
    resultados/piloto.json
    resultados/tablas/piloto_semanal.csv
    resultados/tablas/piloto_sucursales.csv
"""

from __future__ import annotations

import time

import duckdb
import pandas as pd

from src.comun.config import RUTA_ALMACEN, asegurar_directorios, cargar_parametros
from src.comun.resultados import guardar_json, guardar_tabla
from src.piloto.diseno import disenar
from src.piloto.estimacion import estimar
from src.piloto.simulacion import simular_piloto


def ejecutar() -> dict:
    inicio = time.time()
    parametros = cargar_parametros()
    asegurar_directorios()
    cfg = parametros["piloto"]
    con = duckdb.connect(str(RUTA_ALMACEN), read_only=True)
    try:
        print("[1/3] Asignando sucursales de tratamiento y control...")
        asignacion, balance = disenar(con, parametros)
        tratadas = sorted(asignacion.loc[asignacion["tratamiento"] == 1, "sucursal_id"])
        print(f"      tratamiento: {', '.join(tratadas)}")
        print("[2/3] Simulando 24 semanas con choques comunes...")
        panel, _ = simular_piloto(con, parametros, asignacion)
        print("[3/3] Estimando diferencias en diferencias y potencia...")
        resultado = estimar(panel, asignacion, parametros)
        resumen_tiendas = _resumen_tiendas(panel, asignacion)
        guardar_tabla("piloto_semanal", panel)
        guardar_tabla("piloto_sucursales", resumen_tiendas)
        salida = {
            "parametros": {
                "semanas": int(cfg["semanas"]),
                "semanas_pre": int(cfg["semanas_pre"]),
                "n_tratamiento": int(cfg["n_tratamiento"]),
                "efecto_esperado": float(cfg["efecto_esperado"]),
                "semilla": int(cfg["semilla_piloto"]),
            },
            "diseno": {
                "tratamiento": tratadas,
                "control": sorted(
                    asignacion.loc[asignacion["tratamiento"] == 0, "sucursal_id"]
                ),
                "balance": balance.to_dict(orient="records"),
                "sucursales": resumen_tiendas.to_dict(orient="records"),
            },
            "resultado": resultado,
            "tiempo_segundos": round(time.time() - inicio, 1),
        }
        guardar_json("piloto", salida)
        _imprimir(resultado)
        return salida
    finally:
        con.close()


def _resumen_tiendas(panel: pd.DataFrame, asignacion: pd.DataFrame) -> pd.DataFrame:
    agregado = (
        panel.groupby(["sucursal_id", "tratamiento", "post"])
        .agg(fill_rate=("fill_rate", "mean"), unidades=("unidades", "mean"))
        .reset_index()
        .pivot(index=["sucursal_id", "tratamiento"], columns="post")
        .reset_index()
    )
    agregado.columns = [
        "sucursal_id",
        "tratamiento",
        "fill_pre",
        "fill_post",
        "unidades_pre",
        "unidades_post",
    ]
    agregado["cambio_fill_pp"] = (agregado["fill_post"] - agregado["fill_pre"]) * 100
    return asignacion.merge(agregado, on=["sucursal_id", "tratamiento"], how="left")


def _imprimir(resultado: dict) -> None:
    efecto = resultado["efecto_fill_pp"]
    ic = resultado["efecto_fill_ic95"]
    potencia = resultado["potencia"]
    print(
        f"      efecto DiD {efecto:+.2f} pp de fill rate "
        f"(IC95% {ic[0]:+.2f} a {ic[1]:+.2f}; p={resultado['efecto_fill_p']:.4f}); "
        f"tendencia previa p={resultado['tendencia_pre_p']:.2f}; "
        f"MDE {potencia['mde_pp']:.2f} pp con potencia {potencia['potencia_observada']:.2%}"
    )


if __name__ == "__main__":
    ejecutar()
