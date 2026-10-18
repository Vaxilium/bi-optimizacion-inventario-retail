"""Generacion de la demanda potencial diaria por sucursal y SKU.

La demanda potencial es la que existiria con stock infinito. Incluye
estacionalidad semanal, anual y de feriados, promociones con efecto de
adelanto de compras (pull-forward), tendencia, ruido e intermitencia.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.generacion.catalogos import CATEGORIAS, feriados

DIAS_CALENTAMIENTO = 42

_AJUSTE_SEMANAL = {
    "Abarrotes": [0.98, 1.00, 1.00, 1.02, 1.04, 1.06, 1.04],
    "Bebidas": [0.90, 0.90, 0.92, 1.00, 1.12, 1.22, 1.15],
    "Lacteos": [1.00, 1.00, 1.00, 1.02, 1.05, 1.08, 1.05],
    "Panaderia": [1.00, 1.00, 1.00, 1.02, 1.08, 1.12, 1.10],
    "Carnes": [0.90, 0.90, 0.92, 1.00, 1.15, 1.25, 1.05],
    "Frutas y verduras": [0.95, 0.95, 0.98, 1.02, 1.08, 1.15, 1.10],
    "Congelados": [1.00, 1.00, 1.00, 1.00, 1.05, 1.10, 1.08],
    "Limpieza": [1.05, 1.00, 1.00, 1.00, 1.00, 1.02, 1.00],
    "Higiene personal": [1.03, 1.00, 1.00, 1.00, 1.00, 1.02, 1.00],
    "Snacks": [0.95, 0.95, 1.00, 1.05, 1.10, 1.20, 1.15],
}

_AJUSTE_MENSUAL = {
    "Bebidas": {1: 1.15, 2: 1.12, 6: 0.90, 7: 0.90, 8: 0.92},
    "Congelados": {1: 1.08, 2: 1.08, 12: 1.15},
    "Carnes": {1: 1.08, 9: 1.12, 12: 1.20},
    "Frutas y verduras": {1: 1.06, 2: 1.04, 6: 0.95, 7: 0.94},
    "Panaderia": {9: 1.05, 12: 1.10},
    "Snacks": {3: 1.06, 9: 1.08},
    "Abarrotes": {3: 1.05},
    "Lacteos": {3: 1.04},
}
_MENSUAL_BASE = [1.04, 1.00, 1.01, 0.99, 1.01, 0.98, 0.97, 0.99, 1.01, 1.00, 1.03, 1.20]

_FERIADOS_CATEGORIA = {
    "Navidad": {"Carnes": 1.40, "Bebidas": 1.35, "Snacks": 1.30, "Frutas y verduras": 1.20,
                "Panaderia": 1.15, "Congelados": 1.10},
    "Nochebuena": {"Carnes": 1.30, "Bebidas": 1.30, "Snacks": 1.25, "Frutas y verduras": 1.15},
    "Fin de Año": {"Bebidas": 1.40, "Carnes": 1.20, "Snacks": 1.15},
    "Año Nuevo": {"Abarrotes": 0.75, "Bebidas": 0.80, "Carnes": 0.80},
    "Fiestas Patrias": {"Carnes": 1.50, "Bebidas": 1.40, "Snacks": 1.20, "Panaderia": 1.10},
    "Día de la Madre": {"Snacks": 1.25, "Higiene personal": 1.20, "Lacteos": 1.10},
    "Día del Padre": {"Bebidas": 1.15, "Carnes": 1.10},
    "Día del Niño": {"Snacks": 1.20, "Congelados": 1.10},
    "Carnaval": {"Bebidas": 1.20, "Carnes": 1.05},
    "Viernes Santo": {"Carnes": 0.80, "Congelados": 1.20, "Frutas y verduras": 1.10},
    "Jueves Santo": {"Carnes": 0.90, "Congelados": 1.10},
    "Día del Trabajador": {"Bebidas": 0.90, "Snacks": 0.90},
}

_AJUSTE_REGION = {
    "Litoral": {"Bebidas": 1.10, "Frutas y verduras": 1.06, "Congelados": 1.04},
    "Norte": {"Bebidas": 1.06, "Abarrotes": 1.02},
    "Sur": {"Abarrotes": 1.03, "Lacteos": 1.04, "Panaderia": 1.03},
    "Centro": {},
}


def construir_pares(
    dim_producto: pd.DataFrame, dim_sucursal: pd.DataFrame, cfg: dict[str, Any],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Define el surtido: que SKU vende cada sucursal (pares sucursal-SKU)."""
    surtido_min = cfg["generacion"]["surtido_min"]
    surtido_max = cfg["generacion"]["surtido_max"]
    factor_tamano = {"Metropolitana": 0.04, "Grande": 0.0, "Mediana": -0.04}
    filas = []
    for sucursal in dim_sucursal.itertuples():
        for producto in dim_producto.itertuples():
            prob = rng.uniform(surtido_min, surtido_max) + factor_tamano[sucursal.tamano]
            if producto.categoria in ("Frutas y verduras", "Carnes", "Panaderia"):
                prob -= 0.04
            if rng.random() <= min(prob, 0.99):
                filas.append({
                    "sucursal_id": sucursal.sucursal_id,
                    "producto_id": producto.producto_id,
                    "categoria": producto.categoria,
                    "factor_par": float(np.clip(rng.lognormal(0, 0.18), 0.6, 1.6)),
                })
    return pd.DataFrame(filas)


def matriz_promociones(
    pares: pd.DataFrame, promociones: pd.DataFrame, fechas: pd.DatetimeIndex,
    productos: pd.Series, sucursales: pd.Series,
) -> tuple[np.ndarray, np.ndarray]:
    """Construye multiplicadores de demanda y precios diarios por promocion."""
    n_pares, n_dias = len(pares), len(fechas)
    indice = {
        (s, p): i for i, (s, p) in
        enumerate(zip(pares["sucursal_id"], pares["producto_id"]))
    }
    multiplicador = np.ones((n_pares, n_dias), dtype=np.float32)
    precios = np.repeat(
        productos.reindex(pares["producto_id"])["precio_lista"].to_numpy()[:, None].astype(np.float32),
        n_dias, axis=1,
    )
    fecha_cero = fechas[0]
    for fila in promociones.itertuples():
        par = indice.get((fila.sucursal_id, fila.producto_id))
        if par is None:
            continue
        inicio = (pd.Timestamp(fila.fecha_inicio) - fecha_cero).days
        fin = (pd.Timestamp(fila.fecha_fin) - fecha_cero).days
        multiplicador[par, inicio:fin + 1] *= fila.uplift_esperado
        precios[par, inicio:fin + 1] = fila.precio_promocional
        fin_pull = min(n_dias, fin + 5)
        pull = 1 - min(0.30, 0.12 + 0.05 * (fila.uplift_esperado - 1))
        multiplicador[par, fin + 1:fin_pull] *= pull
    return multiplicador, precios


def generar_demanda(
    pares: pd.DataFrame, dim_producto: pd.DataFrame, dim_sucursal: pd.DataFrame,
    params_producto: pd.DataFrame, promociones: pd.DataFrame, cfg: dict[str, Any],
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Genera la demanda potencial diaria y devuelve matrices y metadatos."""
    inicio = pd.Timestamp(cfg["proyecto"]["fecha_inicio"]) - pd.Timedelta(days=DIAS_CALENTAMIENTO)
    fin = pd.Timestamp(cfg["proyecto"]["fecha_fin"])
    fechas = pd.date_range(inicio, fin, freq="D")
    n_dias = len(fechas)

    productos = dim_producto.set_index("producto_id")
    params = params_producto.set_index("producto_id")
    sucursales = dim_sucursal.set_index("sucursal_id")

    base = params.reindex(pares["producto_id"])["demanda_base_diaria"].to_numpy()
    factor_sucursal = sucursales.reindex(pares["sucursal_id"])["factor_demanda"].to_numpy()
    base_par = base * factor_sucursal * pares["factor_par"].to_numpy()
    region_par = sucursales.reindex(pares["sucursal_id"])["region"].to_numpy()
    categoria_par = pares["categoria"].to_numpy()
    prob_inter = params.reindex(pares["producto_id"])["prob_intermitente"].to_numpy()
    clase_par = params.reindex(pares["producto_id"])["rotacion_clase"].to_numpy()
    sigma_base = {"alta": 0.28, "media": 0.40, "baja": 0.62, "muy_baja": 0.80}

    # Factores por categoria y dia: semana, mes, feriados, region.
    categorias = list(CATEGORIAS)
    cat_idx = {c: i for i, c in enumerate(categorias)}
    factors = np.ones((len(categorias), n_dias), dtype=np.float32)
    dow = fechas.dayofweek.to_numpy()
    mes = fechas.month.to_numpy()
    mapa_feriados = _mapa_feriados(fechas)
    for categoria in categorias:
        i = cat_idx[categoria]
        factors[i] *= np.array(_AJUSTE_SEMANAL[categoria], dtype=np.float32)[dow]
        mensual = np.array(_MENSUAL_BASE, dtype=np.float32).copy()
        for m, ajuste in _AJUSTE_MENSUAL.get(categoria, {}).items():
            mensual[m - 1] *= ajuste
        factors[i] *= mensual[mes - 1]
        dec = 1 + (CATEGORIAS[categoria]["dec_navidad"] - 1) * 0.55
        factors[i, mes == 12] *= dec
        for dia, nombre in mapa_feriados:
            multiplicador = _FERIADOS_CATEGORIA.get(nombre, {}).get(categoria, 0.92)
            factors[i, dia] *= multiplicador
    quincena = np.isin(fechas.day.to_numpy(), [14, 15, 16, 29, 30, 31])
    factors *= np.where(quincena, 1.05, 1.0).astype(np.float32)
    trend = np.power(1 + cfg["generacion"]["tendencia_anual"],
                     (np.arange(n_dias) - DIAS_CALENTAMIENTO) / 365.0).astype(np.float32)
    factors *= trend

    # Lambda base por par y dia, con ajuste regional por categoria.
    indice_categoria = np.array([cat_idx[c] for c in categoria_par])
    factores_par = factors[indice_categoria]
    region_mult = np.array([
        _AJUSTE_REGION[r].get(c, 1.0) for r, c in zip(region_par, categoria_par)
    ], dtype=np.float32)
    lam = base_par[:, None] * region_mult[:, None] * factores_par
    lam = np.maximum(lam, 1e-4)

    mult_promos, precios = matriz_promociones(
        pares, promociones, fechas, productos, dim_sucursal["sucursal_id"]
    )
    lam *= mult_promos

    # Ruido multiplicativo e intermitencia.
    sigmas = np.array([sigma_base[c] for c in clase_par], dtype=np.float32)
    ruido = np.exp(rng.normal(
        (-0.5 * sigmas**2)[:, None], sigmas[:, None], size=lam.shape
    ))
    lam = lam * ruido
    activo = rng.random(lam.shape) < prob_inter[:, None]
    lam = np.where(activo, lam / prob_inter[:, None], 0.0)
    demanda = rng.poisson(np.clip(lam, 0, 2000)).astype(np.int32)
    return {
        "fechas": fechas,
        "demanda": demanda,
        "precios": precios,
        "multiplicador_promocion": mult_promos,
    }


def _mapa_feriados(fechas: pd.DatetimeIndex) -> list[tuple[int, str]]:
    mapa = {}
    for anio in range(fechas[0].year, fechas[-1].year + 1):
        for fecha, nombre in feriados(anio):
            mapa[pd.Timestamp(fecha)] = nombre
    return [(i, mapa[fecha]) for i, fecha in enumerate(fechas) if fecha in mapa]
