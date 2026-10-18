"""Evaluacion de censura por quiebre y correccion de la historia observada.

Este es el unico modulo de pronostico autorizado a leer la verdad oculta, y lo hace
solo para evaluar: los modelos se entrenan con ventas observadas y marca de quiebre.
"""

from __future__ import annotations

import duckdb
import numpy as np

from src.comun.config import RUTA_VERDAD


def corregir_historia(
    observado: np.ndarray,
    quiebre: np.ndarray,
    ventana: int = 28,
    cuantil: float = 0.90,
) -> np.ndarray:
    """Imputa los dias con quiebre con un cuantil alto de dias normales del mismo dia de semana.

    El cuantil alto refleja que los quiebres suelen ocurrir en dias de demanda alta.
    """
    observado = np.asarray(observado, dtype=float)
    quiebre = np.asarray(quiebre, dtype=float)
    corregido = observado.copy()
    if not quiebre.any():
        return corregido
    dias_semana = np.arange(len(observado)) % 7
    for posicion in np.flatnonzero(quiebre > 0):
        inicio = max(0, posicion - ventana)
        candidatos = np.flatnonzero(
            (quiebre[inicio:posicion] == 0)
            & (dias_semana[inicio:posicion] == dias_semana[posicion])
        )
        base = observado[inicio:posicion][candidatos] if len(candidatos) else observado[inicio:posicion]
        if len(base):
            corregido[posicion] = np.quantile(base, cuantil)
    return corregido


def cargar_verdad(con: duckdb.DuckDBPyConnection, identificadores: list[str]) -> dict[str, np.ndarray]:
    """Carga la demanda potencial por serie para medir el error fuera de muestra."""
    verdad = con.execute(
        f"SELECT * FROM read_parquet('{(RUTA_VERDAD / 'verdad_demanda.parquet').as_posix()}')"
    ).fetchdf()
    verdad["identificador"] = verdad["sucursal_id"] + "-" + verdad["producto_id"]
    return {
        clave: grupo.sort_values("fecha")["demanda_real"].to_numpy(dtype=float)
        for clave, grupo in verdad[verdad["identificador"].isin(identificadores)].groupby("identificador")
    }
