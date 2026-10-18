"""Ejecuta el analisis exploratorio en SQL y guarda tablas y metricas.

Uso:
    python -m src.analisis_sql.ejecutar [--rapido]

Salidas:
    resultados/tablas/analisis_*.csv
    resultados/analisis.json
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import duckdb
import pandas as pd

from src.comun.config import RUTA_ALMACEN, RUTA_SQL, asegurar_directorios, cargar_parametros
from src.comun.resultados import guardar_json, guardar_tabla
from src.comun.sql import consultar

ANALISIS = [
    ("ventas_mensual", "01_ventas.sql"),
    ("abc_sku", "02_abc.sql"),
    ("quiebres", "03_quiebres.sql"),
    ("promociones", "04_promociones.sql"),
    ("inventario", "05_inventario.sql"),
    ("sucursales", "06_sucursales.sql"),
    ("resumen", "99_resumen.sql"),
]


def ejecutar(modo_rapido: bool = False) -> dict[str, Any]:
    inicio = time.time()
    cargar_parametros(modo_rapido)
    asegurar_directorios()
    con = duckdb.connect(str(RUTA_ALMACEN))
    try:
        tablas = {}
        resumen_df = None
        for nombre, archivo in ANALISIS:
            df = consultar(con, RUTA_SQL / "analisis" / archivo)
            guardar_tabla(f"analisis_{nombre}", df)
            tablas[nombre] = len(df)
            if nombre == "resumen":
                resumen_df = df
            print(f"      {nombre}: {len(df):,} filas")
        resumen = _limpiar(resumen_df.iloc[0].to_dict())
        salida = {
            "resumen": resumen,
            "tablas": tablas,
            "segundos": round(time.time() - inicio, 1),
        }
        guardar_json("analisis", salida)
        _imprimir(resumen)
        return salida
    finally:
        con.close()


ENTEROS = {
    "sku_total", "sku_clase_a", "dias_quiebre", "dias_con_demanda",
    "unidades_totales", "unidades_perdidas", "promociones", "unidades_incrementales",
}


def _limpiar(datos: dict[str, Any]) -> dict[str, Any]:
    limpio = {}
    for clave, valor in datos.items():
        if isinstance(valor, float) and pd.isna(valor):
            limpio[clave] = None
        elif clave in ENTEROS and valor is not None:
            limpio[clave] = int(round(float(valor)))
        elif hasattr(valor, "item"):
            limpio[clave] = valor.item()
        else:
            limpio[clave] = valor
    return limpio


def _imprimir(r: dict[str, Any]) -> None:
    print(
        f"      ventas {r['ventas_totales'] / 1e6:,.1f}M UM | "
        f"quiebre {r['tasa_quiebre']:.1%} | "
        f"perdido {r['margen_perdido'] / 1e6:,.1f}M UM | "
        f"capital baja rotacion {r['capital_share_baja']:.1%} | "
        f"uplift promos {r['uplift_medio']:.0%}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
