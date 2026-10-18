"""Simulacion diaria de las politicas actual y propuesta sobre demanda potencial."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.inventario.contexto import Contexto

DIAS_CALENTAMIENTO = 28


def simular(
    contexto: Contexto,
    demanda: np.ndarray,
    parametros: dict,
    politica: str,
    semilla: int,
) -> dict[str, np.ndarray]:
    cfg = parametros["inventario"]
    pol = parametros["politica_actual"]
    n, dias = demanda.shape
    ventana = int(pol["ventana_media_movil"])
    seguridad = float(pol["dias_seguridad_cobertura"])
    rng = np.random.default_rng(semilla)
    inicial = demanda[:, :DIAS_CALENTAMIENTO].mean(axis=1)
    stock = _stock_inicial(inicial, contexto, pol)
    on_order = np.zeros(n)
    programadas = np.zeros((n, dias + 40))
    venta = np.zeros((n, dias))
    perdida = np.zeros((n, dias))
    stock_cierre = np.zeros((n, dias))
    merma = np.zeros((n, dias))
    pedidos = np.zeros((n, dias))
    quiebre = np.zeros((n, dias), dtype=bool)
    for t in range(dias):
        recepcion = programadas[:, t]
        stock += recepcion
        on_order = np.maximum(on_order - recepcion, 0)
        if t >= ventana:
            pronostico = venta[:, t - ventana:t].mean(axis=1)
            sigma = venta[:, t - ventana:t].std(axis=1)
        else:
            pronostico = inicial
            sigma = inicial * 0.30
        revision = ((t - contexto.fase) % contexto.frecuencia == 0) & (t < dias - 1)
        if politica == "actual":
            cantidad = _cantidad_actual(
                pronostico, contexto, stock + on_order, seguridad
            )
        else:
            cantidad = _cantidad_propuesta(
                pronostico, sigma, contexto, stock + on_order, cfg, seguridad
            )
        cantidad = np.where(revision, cantidad, 0)
        activos = cantidad > 0
        if activos.any():
            filas = np.flatnonzero(activos)
            lead = np.clip(
                np.round(rng.normal(contexto.lead_media[filas], contexto.lead_sd[filas])),
                1, 35,
            ).astype(int)
            llegada = t + lead
            validos = llegada < programadas.shape[1]
            np.add.at(programadas, (filas[validos], llegada[validos]), cantidad[filas][validos])
            on_order[filas] += cantidad[filas]
            pedidos[filas, t] = cantidad[filas]
        disponible = np.floor(np.maximum(stock, 0))
        vendido = np.minimum(demanda[:, t], disponible)
        venta[:, t] = vendido
        perdida[:, t] = demanda[:, t] - vendido
        quiebre[:, t] = (demanda[:, t] > 0) & (demanda[:, t] > disponible)
        stock = np.maximum(stock - vendido, 0)
        pronostico_merma = venta[:, t - ventana:t].mean(axis=1) if t >= ventana else inicial
        objetivo_merma = np.maximum(pronostico_merma, 0.2) * contexto.vida
        sobre_stock = np.maximum(stock - objetivo_merma, 0)
        merma_dia = sobre_stock / contexto.vida + stock * 0.10 / contexto.vida
        merma_dia = np.where(
            contexto.perecedero, np.minimum(merma_dia, stock), 0.0
        )
        stock = np.maximum(stock - merma_dia, 0)
        stock_cierre[:, t] = stock
        merma[:, t] = merma_dia
    return {
        "venta": venta,
        "perdida": perdida,
        "stock_cierre": stock_cierre,
        "merma": merma,
        "pedidos": pedidos,
        "quiebre": quiebre,
    }


def _stock_inicial(inicial: np.ndarray, contexto: Contexto, pol: dict) -> np.ndarray:
    objetivo = inicial * (contexto.lead_media + contexto.frecuencia + float(pol["dias_seguridad_cobertura"]))
    tope = np.maximum(inicial * contexto.vida * 1.15, contexto.presentacion)
    objetivo = np.where(contexto.perecedero, np.minimum(objetivo, tope), objetivo)
    return np.maximum(np.ceil(objetivo / contexto.pack) * contexto.pack, contexto.presentacion)


def _cantidad_actual(
    pronostico: np.ndarray, contexto: Contexto, posicion: np.ndarray, seguridad: float
) -> np.ndarray:
    objetivo = pronostico * (contexto.lead_media + contexto.frecuencia + seguridad)
    tope = np.maximum(pronostico * contexto.vida * 1.15, contexto.presentacion)
    objetivo = np.where(contexto.perecedero, np.minimum(objetivo, tope), objetivo)
    objetivo = np.maximum(np.ceil(objetivo / contexto.pack) * contexto.pack, contexto.presentacion)
    faltante = np.maximum(objetivo - posicion, 0)
    cantidad = np.ceil(faltante / contexto.pack) * contexto.pack
    return np.minimum(cantidad, np.maximum(objetivo * 3, contexto.pack * 4))


def _cantidad_propuesta(
    pronostico: np.ndarray,
    sigma: np.ndarray,
    contexto: Contexto,
    posicion: np.ndarray,
    cfg: dict,
    seguridad: float,
) -> np.ndarray:
    pronostico = pronostico * contexto.factor_censura
    sigma = sigma * contexto.factor_censura
    sigma_lt = np.sqrt(
        contexto.lead_media * sigma**2 + pronostico**2 * contexto.lead_sd**2
    )
    base_actual = pronostico * (
        contexto.lead_media + contexto.frecuencia
        + seguridad
    ) * float(cfg.get("factor_tope_actual", 1.0))
    punto_pedido = np.minimum(
        pronostico * (contexto.lead_media + contexto.frecuencia)
        + contexto.servicio * sigma_lt,
        base_actual,
    )
    eoq = np.sqrt(
        np.maximum(
            2 * pronostico * 365 * float(cfg["costo_orden"])
            / np.maximum(contexto.costo * float(cfg["tasa_almacenamiento_anual"]), 1e-9),
            0,
        )
    )
    eoq = np.minimum(eoq, pronostico * 30)
    objetivo = punto_pedido + eoq
    cobertura_actual = float(cfg["cobertura_maxima_dias"])
    tope = np.maximum(pronostico * cobertura_actual, punto_pedido)
    tope_perecedero = np.maximum(pronostico * contexto.vida * 1.15, punto_pedido)
    tope = np.where(contexto.perecedero, np.minimum(tope, tope_perecedero), tope)
    objetivo = np.minimum(objetivo, np.minimum(tope, base_actual))
    objetivo = np.maximum(objetivo, punto_pedido)
    faltante = np.where(posicion < punto_pedido, objetivo - posicion, 0)
    return np.ceil(np.maximum(faltante, 0) / contexto.pack) * contexto.pack


def metricas(
    resultado: dict[str, np.ndarray], contexto: Contexto, cfg: dict
) -> pd.DataFrame:
    inicio = DIAS_CALENTAMIENTO
    venta = resultado["venta"][:, inicio:]
    perdida = resultado["perdida"][:, inicio:]
    demanda = venta + perdida
    stock = resultado["stock_cierre"][:, inicio:]
    merma = resultado["merma"][:, inicio:]
    pedidos = resultado["pedidos"][:, inicio:]
    quiebre = resultado["quiebre"][:, inicio:]
    unidades = venta.sum(axis=1)
    perdidas = perdida.sum(axis=1)
    dias_con_demanda = (demanda > 0).sum(axis=1)
    dias_quiebre = quiebre.sum(axis=1)
    stock_valor = stock * contexto.costo[:, None]
    marco = pd.DataFrame(
        {
            "venta": unidades,
            "valor_venta": (venta * contexto.precio[:, None]).sum(axis=1),
            "costo_venta": (venta * contexto.costo[:, None]).sum(axis=1),
            "margen_bruto": (venta * contexto.margen[:, None]).sum(axis=1),
            "perdida": perdidas,
            "fill_rate": np.where(
                unidades + perdidas > 0, unidades / np.maximum(unidades + perdidas, 1e-9), 1.0
            ),
            "dias_con_demanda": dias_con_demanda,
            "dias_quiebre": dias_quiebre,
            "tasa_quiebre": np.where(
                dias_con_demanda > 0, dias_quiebre / np.maximum(dias_con_demanda, 1), 0.0
            ),
            "stock_promedio": stock.mean(axis=1),
            "stock_valor_promedio": stock_valor.mean(axis=1),
            "merma_unidades": merma.sum(axis=1),
            "merma_valor": (merma * contexto.costo[:, None]).sum(axis=1),
            "pedidos": (pedidos > 0).sum(axis=1),
            "unidades_pedidas": pedidos.sum(axis=1),
            "costo_orden": (pedidos > 0).sum(axis=1) * float(cfg["costo_orden"]),
            "costo_almacenamiento": stock_valor.sum(axis=1)
            * float(cfg["tasa_almacenamiento_anual"]) / 365,
            "costo_quiebre": perdidas * contexto.margen
            * float(cfg["costo_quiebre_factor_margen"]),
        }
    )
    marco["costo_merma"] = marco["merma_valor"]
    marco["costo_total"] = (
        marco["costo_orden"] + marco["costo_almacenamiento"]
        + marco["costo_quiebre"] + marco["costo_merma"]
    )
    return marco
