"""Simulacion de la dinamica de inventario con la politica actual.

Se simula dia a dia: pedido semanal, recepcion con lead time variable,
venta censurada por el stock disponible y merma por vencimiento en perecederos.
La demanda potencial se recibe ya generada; aqui solo se decide cuanto se vende.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def simular_historia(
    pares: pd.DataFrame, dim_producto: pd.DataFrame, dim_proveedor: pd.DataFrame,
    dim_sucursal: pd.DataFrame, params_producto: pd.DataFrame,
    demanda: np.ndarray, precios: np.ndarray, fechas: pd.DatetimeIndex,
    cfg: dict[str, Any], rng: np.random.Generator,
) -> dict[str, Any]:
    n_pares, n_dias = demanda.shape
    producto = dim_producto.set_index("producto_id")
    proveedor = dim_proveedor.set_index("proveedor_id")
    sucursal = dim_sucursal.set_index("sucursal_id")
    params = params_producto.set_index("producto_id")
    pol = cfg["politica_actual"]

    pack = params.reindex(pares["producto_id"])["pack"].to_numpy().astype(np.float64)
    vida = params.reindex(pares["producto_id"])["vida_util_dias"].to_numpy().astype(np.float64)
    perecedero = producto.reindex(pares["producto_id"])["perecedero"].to_numpy().astype(bool)
    costo = producto.reindex(pares["producto_id"])["costo_unitario"].to_numpy()
    prov_id = producto.reindex(pares["producto_id"])["proveedor_id"].to_numpy()
    lt_media = proveedor.reindex(prov_id)["lead_time_medio_dias"].to_numpy()
    lt_sd = proveedor.reindex(prov_id)["lead_time_sd_dias"].to_numpy()
    factor_sucursal = sucursal.reindex(pares["sucursal_id"])["factor_demanda"].to_numpy()
    base = params.reindex(pares["producto_id"])["demanda_base_diaria"].to_numpy()
    demanda_inicial = np.maximum(base * factor_sucursal * pares["factor_par"].to_numpy(), 0.05)
    clase = params.reindex(pares["producto_id"])["rotacion_clase"].to_numpy()
    presentacion = np.where(
        np.isin(clase, ["baja", "muy_baja"]),
        float(pol.get("packs_presentacion_baja", 3)),
        float(pol.get("packs_presentacion_alta", 2)),
    ) * pack

    ventana = int(pol["ventana_media_movil"])
    seguridad = float(pol["dias_seguridad_cobertura"])
    offset_tienda = {
        s: i % 7 for i, s in enumerate(dim_sucursal["sucursal_id"])
    }
    frecuencia = np.where(
        perecedero & (vida <= 6), int(pol["revision_dias_perecedero_corto"]),
        np.where(perecedero & (vida <= 45), int(pol["revision_dias_perecedero_largo"]),
                 int(pol["revision_dias"])),
    ).astype(int)
    fase = np.array([offset_tienda[s] for s in pares["sucursal_id"]]) % frecuencia

    stock = np.ceil(demanda_inicial * (lt_media + 14) / pack) * pack
    stock = np.clip(stock, presentacion, None)
    on_order = np.zeros(n_pares)

    venta = np.zeros((n_pares, n_dias), dtype=np.int32)
    perdida = np.zeros((n_pares, n_dias), dtype=np.int32)
    stock_cierre = np.zeros((n_pares, n_dias), dtype=np.float32)
    merma = np.zeros((n_pares, n_dias), dtype=np.float32)
    quiebre = np.zeros((n_pares, n_dias), dtype=bool)
    pedido = np.zeros((n_pares, n_dias), dtype=np.int32)
    recepcion = np.zeros((n_pares, n_dias), dtype=np.int32)
    programadas = np.zeros((n_pares, n_dias + 40), dtype=np.float32)
    registro_pedidos: list[tuple] = []

    for t in range(n_dias):
        # 1) Recepcion de pedidos programados.
        rec = programadas[:, t]
        stock = stock + rec
        on_order = np.maximum(on_order - rec, 0)
        recepcion[:, t] = np.round(rec).astype(np.int32)

        # 2) Revision y pedido segun politica actual (una vez por semana por tienda).
        if t >= ventana:
            pronostico = venta[:, t - ventana:t].mean(axis=1)
        else:
            pronostico = demanda_inicial
        filas_pedido = np.flatnonzero(((t - fase) % frecuencia == 0) & (t < n_dias - 1))
        if len(filas_pedido):
            posicion = stock[filas_pedido] + on_order[filas_pedido]
            cobertura = lt_media[filas_pedido] + frecuencia[filas_pedido] + seguridad
            objetivo = pronostico[filas_pedido] * cobertura
            objetivo_perecedero = np.maximum(
                pronostico[filas_pedido] * vida[filas_pedido] * 1.15,
                presentacion[filas_pedido],
            )
            objetivo = np.where(
                perecedero[filas_pedido], np.minimum(objetivo, objetivo_perecedero), objetivo
            )
            objetivo = np.maximum(np.ceil(objetivo / pack[filas_pedido]) * pack[filas_pedido],
                                 presentacion[filas_pedido])
            faltante = np.maximum(objetivo - posicion, 0)
            cantidad = np.ceil(faltante / pack[filas_pedido]) * pack[filas_pedido]
            cantidad = np.minimum(cantidad, np.maximum(objetivo * 3, pack[filas_pedido] * 4))
            activos = cantidad > 0
            if activos.any():
                filas_act = filas_pedido[activos]
                cant_act = cantidad[activos]
                lt = np.clip(
                    np.round(rng.normal(lt_media[filas_act], lt_sd[filas_act])), 1, 35
                ).astype(int)
                for fila, cantidad_i, lead in zip(filas_act, cant_act, lt):
                    llegada = t + lead
                    pedido[fila, t] = int(cantidad_i)
                    registro_pedidos.append((
                        t, fila, int(cantidad_i), int(lead),
                        (fechas[t] + pd.Timedelta(days=int(lead))).date(),
                    ))
                    if llegada < programadas.shape[1]:
                        programadas[fila, llegada] += cantidad_i
                        on_order[fila] += cantidad_i

        # 3) Venta censurada: solo se vende lo que hay en stock.
        disponible = np.floor(np.maximum(stock, 0))
        venta[:, t] = np.minimum(demanda[:, t], disponible).astype(np.int32)
        perdida[:, t] = demanda[:, t] - venta[:, t]
        quiebre[:, t] = (demanda[:, t] > 0) & (demanda[:, t] > disponible)
        stock = np.maximum(stock - venta[:, t], 0)

        # 4) Merma por vencimiento en perecederos (FIFO aproximado por vida util).
        if t >= ventana:
            pronostico = venta[:, t - ventana:t].mean(axis=1)
        else:
            pronostico = demanda_inicial
        objetivo_merma = np.maximum(pronostico, 0.2) * vida
        sobre_stock = np.maximum(stock - objetivo_merma, 0)
        merma_dia = sobre_stock / vida + stock * 0.10 / vida
        merma_dia = np.where(perecedero, np.minimum(merma_dia, stock), 0.0)
        stock = np.maximum(stock - merma_dia, 0)
        merma[:, t] = merma_dia.astype(np.float32)
        stock_cierre[:, t] = stock.astype(np.float32)

    return {
        "venta": venta,
        "perdida": perdida,
        "stock_cierre": stock_cierre,
        "merma": merma,
        "quiebre": quiebre,
        "pedido": pedido,
        "recepcion": recepcion,
        "registro_pedidos": registro_pedidos,
        "costo": costo,
        "pack": pack,
    }
