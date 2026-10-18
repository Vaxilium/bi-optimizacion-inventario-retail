"""Contexto operativo de la simulacion: surtido, costos, lead times y politicas."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import norm

from src.inventario.demanda import cargar_demanda
from src.comun.config import RUTA_CRUDO
from src.pronostico.series import estadisticas_pares, muestrear


@dataclass
class Contexto:
    pares: pd.DataFrame
    demanda: np.ndarray
    pack: np.ndarray
    vida: np.ndarray
    perecedero: np.ndarray
    costo: np.ndarray
    precio: np.ndarray
    margen: np.ndarray
    lead_media: np.ndarray
    lead_sd: np.ndarray
    frecuencia: np.ndarray
    fase: np.ndarray
    clase_abc: np.ndarray
    servicio: np.ndarray
    presentacion: np.ndarray
    factor_censura: float


def construir_contexto(
    con: duckdb.DuckDBPyConnection,
    parametros: dict,
    usar_todas: bool = False,
) -> Contexto:
    """Arma el contexto; por defecto muestrea 240 series y `usar_todas` toma el surtido completo."""
    config = parametros["inventario"]
    pol = parametros["politica_actual"]
    pares = estadisticas_pares(con)
    if usar_todas:
        pares = pares.sort_values(["sucursal_id", "producto_id"]).reset_index(drop=True)
    else:
        pares = muestrear(
            pares, config["simulacion"]["n_series"],
            int(config["simulacion"]["semilla_simulacion"]),
        )
    productos = con.execute("SELECT * FROM dim_producto").fetchdf().set_index("producto_id")
    proveedores = con.execute("SELECT * FROM dim_proveedor").fetchdf().set_index("proveedor_id")
    sucursales = con.execute("SELECT * FROM dim_sucursal").fetchdf()
    operativos = con.execute(
        f"SELECT * FROM read_parquet('{(RUTA_CRUDO / 'params_producto.parquet').as_posix()}')"
    ).fetchdf().set_index("producto_id")
    demanda = cargar_demanda(con, [f"{f.sucursal_id}-{f.producto_id}" for f in pares.itertuples()])
    matriz = np.vstack([demanda[f"{f.sucursal_id}-{f.producto_id}"] for f in pares.itertuples()])
    ids = pares["producto_id"]
    proveedor = productos.reindex(ids)["proveedor_id"].to_numpy()
    vida = productos.reindex(ids)["vida_util_dias"].to_numpy(dtype=float)
    perecedero = productos.reindex(ids)["perecedero"].to_numpy(dtype=bool)
    frecuencia = np.where(
        perecedero & (vida <= 6), int(pol["revision_dias_perecedero_corto"]),
        np.where(perecedero & (vida <= 45), int(pol["revision_dias_perecedero_largo"]),
                 int(pol["revision_dias"])),
    ).astype(int)
    offset = {s: i % 7 for i, s in enumerate(sucursales["sucursal_id"])}
    fase = np.array([offset[s] for s in pares["sucursal_id"]]) % frecuencia
    clase_rotacion = operativos.reindex(ids)["rotacion_clase"].to_numpy()
    pack = operativos.reindex(ids)["pack"].to_numpy(dtype=float)
    presentacion = np.where(
        np.isin(clase_rotacion, ["baja", "muy_baja"]),
        float(pol["packs_presentacion_baja"]),
        float(pol["packs_presentacion_alta"]),
    ) * pack
    niveles = config["nivel_servicio_objetivo"]
    servicio = np.array([norm.ppf(niveles[c]) for c in pares["clase_abc"]])
    margen = (
        productos.reindex(ids)["precio_lista"].to_numpy()
        - productos.reindex(ids)["costo_unitario"].to_numpy()
    )
    factor = _factor_censura(con)
    return Contexto(
        pares=pares,
        demanda=matriz,
        pack=pack,
        vida=vida,
        perecedero=perecedero,
        costo=productos.reindex(ids)["costo_unitario"].to_numpy(dtype=float),
        precio=productos.reindex(ids)["precio_lista"].to_numpy(dtype=float),
        margen=margen,
        lead_media=proveedores.reindex(proveedor)["lead_time_medio_dias"].to_numpy(dtype=float),
        lead_sd=proveedores.reindex(proveedor)["lead_time_sd_dias"].to_numpy(dtype=float),
        frecuencia=frecuencia,
        fase=fase,
        clase_abc=pares["clase_abc"].to_numpy(),
        servicio=servicio,
        presentacion=presentacion,
        factor_censura=factor,
    )


def _factor_censura(con: duckdb.DuckDBPyConnection) -> float:
    fila = con.execute(
        """
        SELECT 1 - SUM(unidades_perdidas_estimadas)
                   / NULLIF(SUM(unidades) + SUM(unidades_perdidas_estimadas), 0)
        FROM mart_kpi_mensual
        """
    ).fetchone()
    tasa = float(fila[0]) if fila[0] else 1.0
    return 1 / tasa if tasa > 0 else 1.0
