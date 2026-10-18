"""Carga de la demanda potencial para simular politicas de inventario.

La simulacion compara politicas sobre la demanda real del generador (verdad oculta).
Las politicas solo observan ventas y quiebres simulados; este modulo no alimenta
ningun modelo de pronostico, solo la evaluacion de politicas.
"""

from __future__ import annotations

import duckdb
import numpy as np

from src.comun.config import RUTA_VERDAD


def cargar_demanda(con: duckdb.DuckDBPyConnection, identificadores: list[str]) -> dict[str, np.ndarray]:
    """Devuelve la demanda diaria potencial por par sucursal-SKU."""
    verdad = con.execute(
        f"SELECT * FROM read_parquet('{(RUTA_VERDAD / 'verdad_demanda.parquet').as_posix()}')"
    ).fetchdf()
    verdad["identificador"] = verdad["sucursal_id"] + "-" + verdad["producto_id"]
    return {
        clave: grupo.sort_values("fecha")["demanda_real"].to_numpy(dtype=float)
        for clave, grupo in verdad[verdad["identificador"].isin(identificadores)].groupby("identificador")
    }
