"""Simulacion del piloto: 12 semanas pre y 12 semanas post con choques comunes."""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from src.inventario.contexto import Contexto, construir_contexto
from src.inventario.simulacion import DIAS_CALENTAMIENTO, simular


def simular_piloto(
    con: duckdb.DuckDBPyConnection,
    parametros: dict,
    asignacion: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve el panel observado y el contrafactual (todos con politica actual)."""
    cfg = parametros["piloto"]
    semanas = int(cfg["semanas"])
    semanas_pre = int(cfg["semanas_pre"])
    total_semanas = semanas + semanas_pre
    contexto = construir_contexto(con, parametros, usar_todas=True)
    demanda = _demanda_piloto(
        contexto,
        int(cfg["semilla_piloto"]),
        DIAS_CALENTAMIENTO + total_semanas * 7,
    )
    actual = simular(
        contexto, demanda, parametros, "actual", int(cfg["semilla_piloto"]) + 1
    )
    propuesta = simular(
        contexto, demanda, parametros, "propuesta", int(cfg["semilla_piloto"]) + 2
    )
    tiendas = sorted(contexto.pares["sucursal_id"].unique())
    actual_semanal = _semanal(actual, contexto, tiendas, total_semanas)
    propuesta_semanal = _semanal(propuesta, contexto, tiendas, total_semanas)
    tratamiento = dict(zip(asignacion["sucursal_id"], asignacion["tratamiento"]))
    filas = []
    for tienda in tiendas:
        for semana in range(1, total_semanas + 1):
            post = int(semana > semanas_pre)
            tratada = int(tratamiento[tienda])
            usar_propuesta = bool(tratada and post)
            filas.append(
                {
                    "sucursal_id": tienda,
                    "semana": semana,
                    "post": post,
                    "tratamiento": tratada,
                    "fill_rate": (
                        propuesta_semanal[tienda]["fill_rate"][semana - 1]
                        if usar_propuesta
                        else actual_semanal[tienda]["fill_rate"][semana - 1]
                    ),
                    "unidades": (
                        propuesta_semanal[tienda]["unidades"][semana - 1]
                        if usar_propuesta
                        else actual_semanal[tienda]["unidades"][semana - 1]
                    ),
                    "fill_rate_actual": actual_semanal[tienda]["fill_rate"][semana - 1],
                    "unidades_actual": actual_semanal[tienda]["unidades"][semana - 1],
                }
            )
    panel = pd.DataFrame(filas)
    contrafactual = panel.copy()
    contrafactual["fill_rate"] = contrafactual["fill_rate_actual"]
    contrafactual["unidades"] = contrafactual["unidades_actual"]
    return panel, contrafactual


def _demanda_piloto(contexto: Contexto, semilla: int, dias: int) -> np.ndarray:
    generador = np.random.default_rng(semilla)
    historico = contexto.demanda.shape[1] // 28 * 28
    bloques = contexto.demanda[:, :historico].reshape(len(contexto.pares), -1, 28)
    cantidad = int(np.ceil(dias / 28))
    indices = generador.integers(0, bloques.shape[1], size=cantidad)
    camino = np.concatenate([bloques[:, i, :] for i in indices], axis=1)
    return camino[:, :dias]


def _semanal(
    resultado: dict[str, np.ndarray],
    contexto: Contexto,
    tiendas: list[str],
    semanas: int,
) -> dict[str, dict[str, np.ndarray]]:
    inicio = DIAS_CALENTAMIENTO
    venta = resultado["venta"][:, inicio:inicio + semanas * 7]
    perdida = resultado["perdida"][:, inicio:inicio + semanas * 7]
    salida = {}
    for tienda in tiendas:
        filas = (contexto.pares["sucursal_id"] == tienda).to_numpy()
        vendidas = venta[filas].reshape(int(filas.sum()), semanas, 7).sum(axis=(0, 2))
        perdidas = perdida[filas].reshape(int(filas.sum()), semanas, 7).sum(axis=(0, 2))
        salida[tienda] = {
            "unidades": vendidas,
            "fill_rate": np.where(
                vendidas + perdidas > 0,
                vendidas / np.maximum(vendidas + perdidas, 1e-9),
                1.0,
            ),
        }
    return salida
