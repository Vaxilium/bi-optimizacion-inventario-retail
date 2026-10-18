"""Orquestador de la generacion de datos sinteticos.

Uso:
    python -m src.generacion.generar_datos [--rapido]

Salidas:
    datos/crudo/*.parquet       capa cruda con 2-3% de defectos inyectados
    datos/verdad_oculta/*       demanda potencial y perdidas (solo validacion)
    datos/muestras/*.csv        muestras pequenas versionadas en git
    resultados/generacion.json  resumen de volumenes y defectos
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.comun.config import (
    RUTA_CRUDO, RUTA_MUESTRAS, RUTA_VERDAD, asegurar_directorios, cargar_parametros,
)
from src.comun.parquet import guardar_parquet
from src.comun.resultados import guardar_json
from src.generacion.demanda import DIAS_CALENTAMIENTO, construir_pares, generar_demanda
from src.generacion.dimensiones import construir_dimensiones
from src.generacion.simulacion import simular_historia
from src.generacion.suciedad import (
    ensuciar_compras, ensuciar_dimensiones, ensuciar_inventario, ensuciar_ventas,
)

COLUMNAS_VENTAS = [
    "fecha", "sucursal_id", "producto_id", "venta_unidades", "precio_unitario",
    "venta_valorizada", "costo_total", "margen_bruto", "en_promocion", "indicador_quiebre",
]
COLUMNAS_INVENTARIO = [
    "fecha", "sucursal_id", "producto_id", "stock_cierre_unidades",
    "stock_valorizado", "merma_unidades", "merma_valorizada",
]
COLUMNAS_COMPRAS = [
    "fecha_pedido", "sucursal_id", "producto_id", "proveedor_id", "unidades_pedido",
    "lead_time_dias", "fecha_recepcion", "estado", "unidades_recibidas",
]


def generar(modo_rapido: bool = False) -> dict:
    inicio_reloj = time.time()
    cfg = cargar_parametros(modo_rapido)
    asegurar_directorios()
    semilla = int(cfg["proyecto"]["semilla"])
    rng = np.random.default_rng(semilla)

    print("[1/5] Construyendo dimensiones...")
    dims = construir_dimensiones(cfg, rng)
    print(f"      {len(dims['dim_producto'])} SKU, {len(dims['dim_sucursal'])} sucursales, "
          f"{len(dims['dim_proveedor'])} proveedores, {len(dims['promociones']):,} promociones")

    print("[2/5] Definiendo surtido y generando demanda potencial...")
    pares = construir_pares(dims["dim_producto"], dims["dim_sucursal"], cfg, rng)
    demanda = generar_demanda(
        pares, dims["dim_producto"], dims["dim_sucursal"], dims["params_producto"],
        dims["promociones"], cfg, rng,
    )
    print(f"      {len(pares):,} pares sucursal-SKU, matriz {demanda['demanda'].shape}")

    print("[3/5] Simulando reposicion, censura de demanda y merma...")
    sim = simular_historia(
        pares, dims["dim_producto"], dims["dim_proveedor"], dims["dim_sucursal"],
        dims["params_producto"], demanda["demanda"], demanda["precios"],
        demanda["fechas"], cfg, np.random.default_rng(semilla + 101),
    )
    corte = DIAS_CALENTAMIENTO
    fechas = demanda["fechas"][corte:]
    hechos = _construir_hechos(dims, pares, demanda, sim, fechas, corte)
    verdad = _construir_verdad(dims, pares, demanda, sim, fechas, corte)

    print("[4/5] Inyectando defectos y escribiendo capa cruda...")
    rng_sucio = np.random.default_rng(semilla + 202)
    ventas_crudo = ensuciar_ventas(hechos["ventas"], cfg, rng_sucio)
    inventario_crudo = ensuciar_inventario(hechos["inventario"], cfg, rng_sucio)
    compras_crudo = ensuciar_compras(hechos["compras"], cfg, rng_sucio)
    dims_crudo = ensuciar_dimensiones(
        {k: dims[k] for k in ("dim_producto", "dim_sucursal", "dim_proveedor")}, rng_sucio
    )
    tablas_crudo = {
        "hechos_ventas_crudo": ventas_crudo[COLUMNAS_VENTAS],
        "hechos_inventario_crudo": inventario_crudo[COLUMNAS_INVENTARIO],
        "hechos_compras_crudo": compras_crudo[COLUMNAS_COMPRAS],
        "dim_producto_crudo": dims_crudo["dim_producto"],
        "dim_sucursal_crudo": dims_crudo["dim_sucursal"],
        "dim_proveedor_crudo": dims_crudo["dim_proveedor"],
        "dim_fecha_crudo": dims["dim_fecha"],
        "promociones_crudo": dims["promociones"],
    }
    tamanos = {}
    for nombre, tabla in tablas_crudo.items():
        ruta = guardar_parquet(tabla, RUTA_CRUDO / f"{nombre}.parquet")
        tamanos[nombre] = {"filas": int(len(tabla)), "mb": round(ruta.stat().st_size / 1e6, 2)}
    guardar_parquet(verdad, RUTA_VERDAD / "verdad_demanda.parquet")
    dims["params_producto"].to_csv(RUTA_VERDAD / "verdad_producto.csv", index=False)
    _muestras(tablas_crudo)

    print("[5/5] Calculando resumen...")
    resumen = _resumen_verdad(verdad, dims["params_producto"], pares, fechas)
    guardar_json("generacion", {
        "volumenes": tamanos,
        "pares": int(len(pares)),
        "dias": int(len(fechas)),
        "rango_fechas": [str(fechas[0].date()), str(fechas[-1].date())],
        "segundos": round(time.time() - inicio_reloj, 1),
        **resumen["observado"],
    })
    with open(RUTA_VERDAD / "verdad_resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen["verdad"], archivo, ensure_ascii=False, indent=2)
    print(f"      listo en {time.time() - inicio_reloj:.1f}s; "
          f"quiebre observado {resumen['observado']['tasa_quiebre_dias_con_demanda']:.1%}")
    return resumen


def _construir_hechos(
    dims: dict, pares: pd.DataFrame, demanda: dict, sim: dict,
    fechas: pd.DatetimeIndex, corte: int,
) -> dict[str, pd.DataFrame]:
    producto = dims["dim_producto"].set_index("producto_id")
    costo_par = producto.reindex(pares["producto_id"])["costo_unitario"].to_numpy()
    precio_lista = producto.reindex(pares["producto_id"])["precio_lista"].to_numpy()
    n_pares, n_dias = sim["venta"].shape
    n_dias = len(fechas)
    venta = sim["venta"][:, corte:]
    perdida = sim["perdida"][:, corte:]
    stock = sim["stock_cierre"][:, corte:]
    merma = sim["merma"][:, corte:]
    quiebre = sim["quiebre"][:, corte:]
    precios = demanda["precios"][:, corte:]
    en_promocion = precios < (precio_lista[:, None] * 0.999)

    fecha_rep = np.tile(fechas.values, n_pares)
    codigos_suc = {s: i for i, s in enumerate(dims["dim_sucursal"]["sucursal_id"])}
    codigos_prod = {p: i for i, p in enumerate(dims["dim_producto"]["producto_id"])}
    suc_codes = np.repeat(pares["sucursal_id"].map(codigos_suc).to_numpy(), n_dias)
    prod_codes = np.repeat(pares["producto_id"].map(codigos_prod).to_numpy(), n_dias)
    suc_cat = pd.Categorical.from_codes(
        suc_codes, categories=dims["dim_sucursal"]["sucursal_id"].astype(str).tolist()
    )
    prod_cat = pd.Categorical.from_codes(
        prod_codes, categories=dims["dim_producto"]["producto_id"].astype(str).tolist()
    )
    venta_flat = venta.ravel()
    precio_flat = precios.ravel()
    df_ventas = pd.DataFrame({
        "fecha": fecha_rep,
        "sucursal_id": suc_cat,
        "producto_id": prod_cat,
        "venta_unidades": venta_flat.astype(np.int32),
        "precio_unitario": precio_flat.astype(np.float32),
        "venta_valorizada": (venta_flat * precio_flat).astype(np.float32),
        "costo_total": (venta_flat * np.repeat(costo_par, n_dias)).astype(np.float32),
        "margen_bruto": (venta_flat * (precio_flat - np.repeat(costo_par, n_dias))).astype(np.float32),
        "en_promocion": en_promocion.ravel(),
        "indicador_quiebre": quiebre.ravel(),
    })
    stock_flat = stock.ravel()
    df_inventario = pd.DataFrame({
        "fecha": fecha_rep,
        "sucursal_id": suc_cat,
        "producto_id": prod_cat,
        "stock_cierre_unidades": np.round(stock_flat, 2),
        "stock_valorizado": np.round(stock_flat * np.repeat(costo_par, n_dias), 2),
        "merma_unidades": np.round(merma.ravel(), 2),
        "merma_valorizada": np.round(merma.ravel() * np.repeat(costo_par, n_dias), 2),
    })
    pedidos = pd.DataFrame(
        sim["registro_pedidos"], columns=["t", "par", "unidades_pedido", "lead_time_dias", "recepcion"]
    )
    pedidos = pedidos[pedidos["t"] >= corte].copy()
    pedidos["fecha_pedido"] = demanda["fechas"].to_numpy()[pedidos["t"].to_numpy()]
    pedidos["sucursal_id"] = pares["sucursal_id"].to_numpy()[pedidos["par"].to_numpy()]
    pedidos["producto_id"] = pares["producto_id"].to_numpy()[pedidos["par"].to_numpy()]
    pedidos["proveedor_id"] = producto.reindex(pedidos["producto_id"])["proveedor_id"].to_numpy()
    pedidos["fecha_recepcion"] = pd.to_datetime(pedidos["recepcion"])
    fin = fechas[-1]
    pedidos["estado"] = np.where(pedidos["fecha_recepcion"] <= fin, "recibido", "en_transito")
    pedidos["unidades_recibidas"] = np.where(
        pedidos["estado"] == "recibido", pedidos["unidades_pedido"], 0
    )
    df_compras = pedidos[COLUMNAS_COMPRAS].reset_index(drop=True)
    return {"ventas": df_ventas, "inventario": df_inventario, "compras": df_compras}


def _construir_verdad(
    dims: dict, pares: pd.DataFrame, demanda: dict, sim: dict,
    fechas: pd.DatetimeIndex, corte: int,
) -> pd.DataFrame:
    n_pares, n_dias = sim["venta"][:, corte:].shape
    suc_codes = np.repeat(pares["sucursal_id"].map(
        {s: i for i, s in enumerate(dims["dim_sucursal"]["sucursal_id"])}).to_numpy(), n_dias)
    prod_codes = np.repeat(pares["producto_id"].map(
        {p: i for i, p in enumerate(dims["dim_producto"]["producto_id"])}).to_numpy(), n_dias)
    return pd.DataFrame({
        "fecha": np.tile(fechas.values, n_pares),
        "sucursal_id": pd.Categorical.from_codes(
            suc_codes, categories=dims["dim_sucursal"]["sucursal_id"].astype(str).tolist()),
        "producto_id": pd.Categorical.from_codes(
            prod_codes, categories=dims["dim_producto"]["producto_id"].astype(str).tolist()),
        "demanda_real": demanda["demanda"][:, corte:].ravel().astype(np.int32),
        "venta_observada": sim["venta"][:, corte:].ravel().astype(np.int32),
        "venta_perdida": sim["perdida"][:, corte:].ravel().astype(np.int32),
        "quiebre": sim["quiebre"][:, corte:].ravel(),
    })


def _muestras(tablas: dict[str, pd.DataFrame]) -> None:
    RUTA_MUESTRAS.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in tablas.items():
        tabla.head(300).to_csv(RUTA_MUESTRAS / f"{nombre}_muestra.csv", index=False)


def _resumen_verdad(
    verdad: pd.DataFrame, params: pd.DataFrame, pares: pd.DataFrame, fechas: pd.DatetimeIndex,
) -> dict:
    clase = params.set_index("producto_id")["rotacion_clase"]
    verdad = verdad.assign(rotacion=verdad["producto_id"].map(clase))
    con_demanda = verdad["demanda_real"] > 0
    observado = {
        "tasa_quiebre_dias_con_demanda": float(verdad["quiebre"].sum() / max(con_demanda.sum(), 1)),
        "dias_con_demanda": int(con_demanda.sum()),
        "unidades_vendidas": int(verdad["venta_observada"].sum()),
        "unidades_perdidas": int(verdad["venta_perdida"].sum()),
    }
    por_clase = verdad.groupby("rotacion", observed=True).agg(
        demanda=("demanda_real", "sum"), perdida=("venta_perdida", "sum"),
        dias=("demanda_real", "size"), quiebres=("quiebre", "sum"),
    )
    por_clase["tasa_quiebre"] = por_clase["quiebres"] / por_clase["dias"]
    por_clase["tasa_perdida"] = por_clase["perdida"] / por_clase["demanda"].clip(lower=1)
    return {
        "observado": observado,
        "verdad": {
            "tasa_quiebre_por_rotacion": por_clase["tasa_quiebre"].round(4).to_dict(),
            "tasa_perdida_por_rotacion": por_clase["tasa_perdida"].round(4).to_dict(),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    generar(modo_rapido=args.rapido)
