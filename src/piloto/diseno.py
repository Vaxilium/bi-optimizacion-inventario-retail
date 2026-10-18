"""Asignacion estratificada de sucursales y balance del piloto."""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd



def linea_base(con: duckdb.DuckDBPyConnection, semanas: int = 12) -> pd.DataFrame:
    """Resume unidades y tasa de quiebre de las ultimas semanas historicas por sucursal."""
    filas = con.execute(
        """
        SELECT fecha, sucursal_id, unidades, quiebres, observaciones
        FROM mart_ventas_sucursal_dia
        ORDER BY fecha
        """
    ).fetchdf()
    ultima = filas["fecha"].max()
    inicio = ultima - pd.Timedelta(weeks=semanas)
    corte = filas[filas["fecha"] > inicio]
    resumen = (
        corte.groupby("sucursal_id")
        .agg(
            unidades_base=("unidades", "sum"),
            quiebres_base=("quiebres", "sum"),
            observaciones_base=("observaciones", "sum"),
        )
        .reset_index()
    )
    resumen["tasa_quiebre_base"] = (
        resumen["quiebres_base"] / resumen["observaciones_base"].clip(lower=1)
    )
    dimensiones = con.execute(
        "SELECT sucursal_id, nombre_sucursal, tamano, factor_demanda FROM dim_sucursal"
    ).fetchdf()
    return resumen.merge(dimensiones, on="sucursal_id", how="left")


def asignar(resumen: pd.DataFrame, n_tratamiento: int, semilla: int) -> pd.DataFrame:
    """Asigna tratamiento dentro de bloques de tamano comparable (estratificacion)."""
    datos = resumen.sort_values("unidades_base").reset_index(drop=True)
    generador = np.random.default_rng(semilla)
    datos["tratamiento"] = 0
    bloques = np.array_split(np.arange(len(datos)), n_tratamiento)
    for bloque in bloques:
        elegido = int(generador.choice(bloque))
        datos.loc[elegido, "tratamiento"] = 1
    return datos.sort_values("sucursal_id").reset_index(drop=True)


def balance(datos: pd.DataFrame) -> pd.DataFrame:
    """Compara linea base entre tratamiento y control con diferencia estandarizada."""
    filas = []
    for variable in ["unidades_base", "tasa_quiebre_base", "factor_demanda"]:
        tratados = datos.loc[datos["tratamiento"] == 1, variable]
        controles = datos.loc[datos["tratamiento"] == 0, variable]
        desvio = datos[variable].std(ddof=1)
        diferencia = float(tratados.mean() - controles.mean())
        filas.append(
            {
                "variable": variable,
                "tratamiento": float(tratados.mean()),
                "control": float(controles.mean()),
                "diferencia": diferencia,
                "diferencia_estandarizada": diferencia / desvio if desvio else 0.0,
            }
        )
    return pd.DataFrame(filas)


def disenar(con: duckdb.DuckDBPyConnection, parametros: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = parametros["piloto"]
    resumen = linea_base(con, int(cfg["semanas_pre"]))
    datos = asignar(resumen, int(cfg["n_tratamiento"]), int(cfg["semilla_piloto"]))
    return datos, balance(datos)
