"""Ejecucion de archivos SQL con multiples sentencias sobre DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb

import pandas as pd


def ejecutar_archivo(con: duckdb.DuckDBPyConnection, ruta: Path) -> None:
    """Ejecuta cada sentencia del archivo, ignorando bloques de solo comentarios."""
    contenido = ruta.read_text(encoding="utf-8")
    for sentencia in contenido.split(";"):
        codigo = "\n".join(
            linea for linea in sentencia.splitlines()
            if not linea.strip().startswith("--")
        ).strip()
        if not codigo:
            continue
        try:
            con.execute(codigo)
        except duckdb.Error as exc:
            raise RuntimeError(
                f"Error en {ruta.name}: {exc}\n{codigo[:300]}"
            ) from exc


def consultar(con: duckdb.DuckDBPyConnection, ruta: Path) -> pd.DataFrame:
    """Ejecuta un archivo SQL y devuelve el resultado de su ultima sentencia."""
    ejecutar_archivo(con, ruta)
    return con.fetchdf()
