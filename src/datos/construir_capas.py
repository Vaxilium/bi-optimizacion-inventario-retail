"""Construye las capas crudo -> staging -> nucleo -> marts sobre DuckDB.

Uso:
    python -m src.datos.construir_capas [--rapido]

Salidas:
    datos/staging/*.parquet, datos/nucleo/*.parquet, datos/marts/*.parquet
    resultados/capa_datos.json, resultados/contratos.json
    docs/03-capa-de-datos.md
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import duckdb

from src.comun.config import (
    RUTA_ALMACEN, RUTA_CRUDO, RUTA_MARTS, RUTA_MUESTRAS, RUTA_NUCLEO,
    RUTA_SQL, RUTA_STAGING, asegurar_directorios, cargar_parametros,
)
from src.comun.sql import ejecutar_archivo
from src.datos.calidad import construir_bitacora
from src.datos.documentar import generar_documento_datos, guardar_resumen_capa
from src.datos.validar_contratos import validar_contratos

CRUDO = [
    "hechos_ventas", "hechos_inventario", "hechos_compras", "dim_producto",
    "dim_sucursal", "dim_proveedor", "dim_fecha", "promociones",
]
STAGING = [
    "dim_proveedor", "dim_producto", "dim_sucursal", "dim_fecha", "promociones",
    "promo_dias", "ventas", "inventario", "compras",
]
NUCLEO = [
    "dim_fecha", "dim_producto", "dim_sucursal", "dim_proveedor", "dim_promociones",
    "nucleo_hechos_ventas", "nucleo_hechos_inventario", "nucleo_hechos_compras",
]
MARTS = [
    "mart_kpi_mensual", "mart_sucursal_mes", "mart_categoria_mes", "mart_categoria_dia",
    "mart_sku_resumen", "mart_promociones_efecto", "mart_quiebres_producto_mes",
    "mart_ventas_sucursal_dia",
]


def construir(modo_rapido: bool = False) -> dict:
    inicio = time.time()
    cargar_parametros(modo_rapido)
    asegurar_directorios()
    RUTA_ALMACEN.unlink(missing_ok=True)
    con = duckdb.connect(str(RUTA_ALMACEN))
    con.execute("PRAGMA threads=4")
    try:
        _registrar_crudo(con)
        print("[1/4] Staging: limpieza, normalizacion e imputacion...")
        _ejecutar_sql(con, RUTA_SQL / "staging")
        _materializar(con, RUTA_STAGING, [f"stg_{n}" for n in STAGING])
        print("[2/4] Nucleo: modelo en estrella...")
        _ejecutar_sql(con, RUTA_SQL / "nucleo")
        _materializar(con, RUTA_NUCLEO, NUCLEO)
        print("[3/4] Marts: agregados para analisis y tablero...")
        _ejecutar_sql(con, RUTA_SQL / "marts")
        _materializar(con, RUTA_MARTS, MARTS)
        print("[4/4] Contratos, bitacora de calidad y documentacion...")
        volumenes = _volumenes()
        filas_limpias = {
            "hechos_ventas": _contar(con, "stg_ventas"),
            "hechos_inventario": _contar(con, "stg_inventario"),
            "hechos_compras": _contar(con, "stg_compras"),
            "dim_producto": _contar(con, "stg_dim_producto"),
            "dim_sucursal": _contar(con, "stg_dim_sucursal"),
            "dim_proveedor": _contar(con, "stg_dim_proveedor"),
        }
        calidad = construir_bitacora(con, filas_limpias)
        validar_contratos(con)
        contratos = _leer_json("contratos")
        total_crudas = sum(v["filas_crudas"] for v in calidad.values())
        total_afectadas = sum(v["filas_afectadas"] for v in calidad.values())
        capa = {
            "volumenes": volumenes,
            "calidad": calidad,
            "contratos": contratos,
            "tasa_afectadas_global": total_afectadas / total_crudas if total_crudas else 0,
            "segundos": round(time.time() - inicio, 1),
        }
        guardar_resumen_capa(capa)
        generar_documento_datos(capa)
        _muestras_nucleo(con)
        print(f"      capas construidas en {capa['segundos']}s; "
              f"defectos {capa['tasa_afectadas_global']:.2%}; "
              f"contratos {contratos['chequeos'] - contratos['fallidos']}/{contratos['chequeos']} OK")
        return capa
    finally:
        con.close()


def _registrar_crudo(con: duckdb.DuckDBPyConnection) -> None:
    for nombre in CRUDO:
        ruta = (RUTA_CRUDO / f"{nombre}_crudo.parquet").as_posix()
        con.execute(
            f"CREATE OR REPLACE VIEW crudo_{nombre} AS "
            f"SELECT * FROM read_parquet('{ruta}')"
        )


def _ejecutar_sql(con: duckdb.DuckDBPyConnection, carpeta: Path) -> None:
    for archivo in sorted(carpeta.glob("*.sql")):
        ejecutar_archivo(con, archivo)


def _materializar(con: duckdb.DuckDBPyConnection, carpeta: Path, nombres: list[str]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre in nombres:
        ruta = (carpeta / f"{nombre}.parquet").as_posix()
        con.execute(
            f"COPY (SELECT * FROM {nombre}) TO '{ruta}' "
            f"(FORMAT PARQUET, COMPRESSION zstd)"
        )
        con.execute(
            f"CREATE OR REPLACE VIEW {nombre} AS SELECT * FROM read_parquet('{ruta}')"
        )


def _volumenes() -> dict[str, dict]:
    salida = {}
    for capa, carpeta in (("staging", RUTA_STAGING), ("nucleo", RUTA_NUCLEO), ("marts", RUTA_MARTS)):
        for archivo in sorted(carpeta.glob("*.parquet")):
            con = duckdb.connect()
            try:
                filas = con.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{archivo.as_posix()}')"
                ).fetchone()[0]
            finally:
                con.close()
            salida[archivo.stem] = {
                "capa": capa,
                "filas": int(filas),
                "mb": round(archivo.stat().st_size / 1e6, 2),
            }
    return salida


def _contar(con: duckdb.DuckDBPyConnection, tabla: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0])


def _leer_json(nombre: str) -> dict:
    import json
    from src.comun.config import RUTA_RESULTADOS
    with open(RUTA_RESULTADOS / f"{nombre}.json", encoding="utf-8") as archivo:
        return json.load(archivo)


def _muestras_nucleo(con: duckdb.DuckDBPyConnection) -> None:
    RUTA_MUESTRAS.mkdir(parents=True, exist_ok=True)
    for tabla in NUCLEO:
        ruta = RUTA_MUESTRAS / f"{tabla}_muestra.csv"
        con.execute(f"COPY (SELECT * FROM {tabla} LIMIT 300) TO '{ruta.as_posix()}' (HEADER, DELIMITER ',')")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    construir(modo_rapido=args.rapido)
