"""Escritura y lectura de Parquet con DuckDB (sin dependencias adicionales)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


def guardar_parquet(tabla: pd.DataFrame, ruta: Path, compresion: str = "zstd") -> Path:
    """Guarda un DataFrame como Parquet usando DuckDB como motor de escritura."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    copia = tabla.copy()
    for columna in copia.columns:
        if copia[columna].dtype == object:
            copia[columna] = copia[columna].map(
                lambda valor: str(valor) if isinstance(valor, np.str_) else valor
            )
    con = duckdb.connect()
    try:
        con.register("df_temporal", copia)
        con.execute(
            f"COPY (SELECT * FROM df_temporal) TO '{ruta.as_posix()}' "
            f"(FORMAT PARQUET, COMPRESSION {compresion})"
        )
    finally:
        con.close()
    return ruta


def consultar_parquet(ruta: Path) -> pd.DataFrame:
    """Lee un Parquet completo a pandas."""
    con = duckdb.connect()
    try:
        return con.execute(f"SELECT * FROM read_parquet('{ruta.as_posix()}')").fetchdf()
    finally:
        con.close()
