"""Construccion del modelo dimensional (dimensiones) y parametros internos de demanda."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from src.generacion.catalogos import (
    CATEGORIAS, CIUDADES, MARCAS, NOMBRES_PROVEEDORES, feriados,
)


def construir_dimensiones(cfg: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    """Genera todas las dimensiones y los parametros internos del generador."""
    dim_proveedor = _proveedores(cfg, rng)
    dim_producto, params_producto = _productos(cfg, dim_proveedor, rng)
    dim_sucursal = _sucursales(cfg, rng)
    dim_fecha = _fechas(cfg)
    promociones = _promociones(dim_producto, dim_sucursal, cfg, rng)
    return {
        "dim_producto": dim_producto,
        "dim_proveedor": dim_proveedor,
        "dim_sucursal": dim_sucursal,
        "dim_fecha": dim_fecha,
        "promociones": promociones,
        "params_producto": params_producto,
    }


def _productos(
    cfg: dict[str, Any], dim_proveedor: pd.DataFrame, rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_sku = cfg["generacion"]["n_sku"]
    categorias = list(CATEGORIAS)
    proveedores_por_categoria = {
        categoria: grupo["proveedor_id"].to_numpy()
        for categoria, grupo in dim_proveedor.groupby("categoria_principal")
    }
    todos_proveedores = dim_proveedor["proveedor_id"].to_numpy()
    # Distribucion de SKU por categoria: abarrotes y bebidas pesan mas.
    pesos = np.array([0.16, 0.13, 0.11, 0.08, 0.09, 0.11, 0.07, 0.09, 0.08, 0.08])
    pesos = pesos / pesos.sum()
    asignadas = rng.choice(categorias, size=n_sku, p=pesos)
    filas, params = [], []
    contador = 1
    for categoria_cruda in asignadas:
        categoria = str(categoria_cruda)
        info = CATEGORIAS[categoria]
        subcategoria = str(rng.choice(info["subcategorias"]))
        nombre_base = str(rng.choice(info["nombres"]))
        tamano = str(rng.choice(info["tamanos"]))
        marca = str(rng.choice(MARCAS))
        es_perecedero = bool(rng.random() < info["perecible"])
        vida = int(rng.integers(info["vida_util"][0], info["vida_util"][1] + 1))
        if not es_perecedero:
            vida = max(vida, 180)
        margen = float(rng.uniform(*info["margen"]))
        costo = float(np.round(rng.uniform(*info["costo"]), 2))
        precio = float(np.round(costo / (1 - margen), 1))
        proveedor_id = str(rng.choice(
            proveedores_por_categoria.get(categoria, todos_proveedores)
        ))
        filas.append({
            "producto_id": f"SKU-{contador:04d}",
            "nombre_producto": f"{marca} {nombre_base} {tamano}",
            "categoria": categoria,
            "subcategoria": subcategoria,
            "marca": marca,
            "proveedor_id": proveedor_id,
            "contenido": tamano,
            "perecedero": es_perecedero,
            "vida_util_dias": vida,
            "costo_unitario": costo,
            "precio_lista": precio,
            "unidad_medida": "unidad",
        })
        params.append({
            "producto_id": f"SKU-{contador:04d}",
            "categoria": categoria,
            "perecedero": es_perecedero,
            "vida_util_dias": vida,
            "pack": int(rng.integers(info["pack"][0], info["pack"][1] + 1)),
        })
        contador += 1
    dim = pd.DataFrame(filas)
    dim_params = pd.DataFrame(params)

    # Clase de rotacion y demanda base diaria por sucursal promedio (cadena inventada).
    mezcla = np.array(cfg["generacion"]["mezcla_rotacion"], dtype=float)
    clases = rng.choice(["alta", "media", "baja", "muy_baja"], size=len(dim), p=mezcla / mezcla.sum())
    medianas = {"alta": 38.0, "media": 8.5, "baja": 2.0, "muy_baja": 0.55}
    sigmas = {"alta": 0.55, "media": 0.75, "baja": 0.95, "muy_baja": 1.15}
    prob_intermitente = {"alta": 1.0, "media": 1.0, "baja": 0.62, "muy_baja": 0.18}
    base = np.array([
        medianas[c] * np.exp(rng.normal(0, sigmas[c])) for c in clases
    ])
    # Las carnes y frutas rotan mas por su alta perecibilidad; ajuste de categoria.
    multiplicador_categoria = {
        "Abarrotes": 1.10, "Bebidas": 1.25, "Lacteos": 1.05, "Panaderia": 1.15,
        "Carnes": 0.85, "Frutas y verduras": 1.00, "Congelados": 0.70,
        "Limpieza": 0.80, "Higiene personal": 0.65, "Snacks": 0.95,
    }
    dim_params["rotacion_clase"] = clases
    dim_params["demanda_base_diaria"] = np.round(
        base * dim_params["categoria"].map(multiplicador_categoria), 3
    )
    dim_params["prob_intermitente"] = [prob_intermitente[c] for c in clases]
    dim_params["factor_navidad"] = dim_params["categoria"].map(
        {k: v["dec_navidad"] for k, v in CATEGORIAS.items()}
    )
    return dim, dim_params


def _proveedores(cfg: dict[str, Any], rng: np.random.Generator) -> pd.DataFrame:
    n = cfg["generacion"]["n_proveedores"]
    nombres = NOMBRES_PROVEEDORES[:n]
    categorias = list(CATEGORIAS)
    filas = []
    for i, nombre in enumerate(nombres, start=1):
        categoria = categorias[(i - 1) % len(categorias)]
        perecedero = CATEGORIAS[categoria]["perecible"] > 0.5
        if perecedero:
            lead_medio = float(rng.uniform(1.0, 4.0))
            lead_sd = float(rng.uniform(0.3, 1.2))
        else:
            lead_medio = float(rng.uniform(6, 18))
            lead_sd = float(rng.uniform(1.0, 3.5))
        filas.append({
            "proveedor_id": f"PRV-{i:03d}",
            "nombre_proveedor": nombre,
            "categoria_principal": categoria,
            "lead_time_medio_dias": round(lead_medio, 1),
            "lead_time_sd_dias": round(lead_sd, 1),
            "fiabilidad": round(float(rng.uniform(0.85, 0.99)), 2),
            "unidad_minima_pedido": int(rng.choice([6, 8, 12, 18, 24])),
            "condicion_pago": str(rng.choice(["contado", "30 dias", "45 dias", "60 dias"])),
        })
    return pd.DataFrame(filas)


def _sucursales(cfg: dict[str, Any], rng: np.random.Generator) -> pd.DataFrame:
    filas = []
    tamanos = ["Metropolitana"] * 3 + ["Grande"] * 5 + ["Mediana"] * 4
    rng.shuffle(tamanos)
    factores = {"Metropolitana": (1.25, 1.55), "Grande": (0.95, 1.20), "Mediana": (0.62, 0.88)}
    for i, ((ciudad, region), tamano) in enumerate(zip(CIUDADES, tamanos), start=1):
        factor = float(rng.uniform(*factores[tamano]))
        filas.append({
            "sucursal_id": f"SUC-{i:02d}",
            "nombre_sucursal": f"Horizonte {ciudad}",
            "ciudad": ciudad,
            "region": region,
            "tipo_tienda": str(rng.choice(["Hipermercado", "Supermercado", "Express"])),
            "tamano": tamano,
            "superficie_m2": int(factor * 1400 + rng.integers(-150, 250)),
            "factor_demanda": round(factor, 3),
            "fecha_apertura": str(dt.date(2010 + i % 10, 1 + i % 12, 1 + i)),
        })
    return pd.DataFrame(filas)


def _fechas(cfg: dict[str, Any]) -> pd.DataFrame:
    inicio = pd.Timestamp(cfg["proyecto"]["fecha_inicio"])
    fin = pd.Timestamp(cfg["proyecto"]["fecha_fin"])
    fechas = pd.date_range(inicio, fin, freq="D")
    mapa_feriados = {}
    for anio in range(inicio.year, fin.year + 1):
        for fecha, nombre in feriados(anio):
            mapa_feriados[pd.Timestamp(fecha)] = nombre
    nombres_dia = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    df = pd.DataFrame({"fecha": fechas})
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia"] = df["fecha"].dt.day
    df["trimestre"] = df["fecha"].dt.quarter
    df["dia_semana"] = df["fecha"].dt.dayofweek + 1
    df["nombre_dia"] = df["dia_semana"].map(dict(enumerate(nombres_dia, start=1)))
    df["semana_iso"] = df["fecha"].dt.isocalendar().week.astype(int)
    df["es_fin_de_semana"] = df["dia_semana"].isin([6, 7])
    df["es_feriado"] = df["fecha"].isin(mapa_feriados)
    df["nombre_feriado"] = df["fecha"].map(mapa_feriados).fillna("")
    df["es_quincena"] = df["dia"].isin([14, 15, 16, 29, 30, 31])
    df["temporada"] = df["mes"].map(
        {12: "Navidad", 1: "Verano", 2: "Verano", 3: "Verano", 6: "Invierno",
         7: "Invierno", 8: "Invierno", 9: "Fiestas Patrias"}
    ).fillna("Temporada normal")
    return df


def _promociones(
    dim_producto: pd.DataFrame, dim_sucursal: pd.DataFrame, cfg: dict[str, Any],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Eventos promocionales por SKU con participacion parcial de sucursales."""
    inicio = pd.Timestamp(cfg["proyecto"]["fecha_inicio"])
    fin = pd.Timestamp(cfg["proyecto"]["fecha_fin"])
    total_dias = (fin - inicio).days + 1
    sucursales = dim_sucursal["sucursal_id"].to_numpy()
    filas = []
    contador = 1
    tipos = [
        ("descuento_10", 0.10, 1.35), ("descuento_15", 0.15, 1.50),
        ("descuento_20", 0.20, 1.70), ("descuento_25", 0.25, 1.85),
        ("dos_por_uno", 0.50, 2.20), ("tres_por_dos", 0.33, 1.95),
    ]
    for producto_id, fila in dim_producto.set_index("producto_id").iterrows():
        n_eventos = int(rng.poisson(3.6))
        base = fila["precio_lista"]
        for _ in range(n_eventos):
            duracion = int(rng.integers(3, 8))
            inicio_dia = int(rng.integers(10, total_dias - duracion - 10))
            fecha_inicio = inicio + pd.Timedelta(days=inicio_dia)
            fecha_fin = fecha_inicio + pd.Timedelta(days=duracion - 1)
            probabilidad_participacion = rng.uniform(0.45, 0.8)
            participantes = rng.choice(
                sucursales, size=max(2, int(len(sucursales) * probabilidad_participacion)),
                replace=False,
            )
            tipo, descuento, uplift = tipos[int(rng.integers(0, len(tipos)))]
            for sucursal_id in participantes:
                filas.append({
                    "promocion_id": f"PRO-{contador:06d}",
                    "producto_id": producto_id,
                    "sucursal_id": sucursal_id,
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "tipo_promocion": tipo,
                    "descuento_pct": descuento,
                    "precio_promocional": round(base * (1 - descuento), 1),
                    "uplift_esperado": uplift,
                })
                contador += 1
    return pd.DataFrame(filas)
