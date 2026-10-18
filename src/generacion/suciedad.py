"""Inyeccion controlada de datos sucios en la capa cruda.

La tasa global objetivo es 2-3% de filas afectadas. Los conteos exactos de
cada problema los detecta la capa de staging durante la limpieza; este modulo
solo introduce los defectos con semilla fija.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def ensuciar_ventas(df: pd.DataFrame, cfg: dict[str, Any], rng: np.random.Generator) -> pd.DataFrame:
    n = len(df)
    df = df.copy()
    # Codigos inconsistentes (minusculas y espacios): se normalizan en staging.
    producto = df["producto_id"]
    if isinstance(producto.dtype, pd.CategoricalDtype):
        variantes = [str(p).lower() + " " for p in producto.cat.categories]
        df["producto_id"] = producto.cat.add_categories(variantes)
    filas = rng.choice(n, size=int(n * 0.0045), replace=False)
    df.loc[df.index[filas], "producto_id"] = (
        df.loc[df.index[filas], "producto_id"].astype(str).str.lower() + " "
    )
    # Nulos en medidas y en la clave de sucursal.
    filas = rng.choice(n, size=int(n * 0.0035), replace=False)
    df.loc[df.index[filas], "venta_unidades"] = np.nan
    filas = rng.choice(n, size=int(n * 0.0025), replace=False)
    df.loc[df.index[filas], "precio_unitario"] = np.nan
    filas = rng.choice(n, size=int(n * 0.0010), replace=False)
    df.loc[df.index[filas], "sucursal_id"] = np.nan
    # Cantidades negativas espurias.
    filas = rng.choice(n, size=int(n * 0.0025), replace=False)
    df.loc[df.index[filas], "venta_unidades"] = -np.abs(
        rng.integers(1, 50, size=len(filas))
    ).astype(float)
    # Fechas futuras (fuera del periodo del proyecto).
    filas = rng.choice(n, size=int(n * 0.0010), replace=False)
    df.loc[df.index[filas], "fecha"] = pd.Timestamp("2026-01-15")
    # Duplicados exactos.
    duplicados = df.iloc[rng.choice(n, size=int(n * 0.012), replace=False)]
    df = pd.concat([df, duplicados], ignore_index=True)
    return df.sample(frac=1.0, random_state=int(cfg["proyecto"]["semilla"]) % 2**31).reset_index(drop=True)


def ensuciar_inventario(df: pd.DataFrame, cfg: dict[str, Any], rng: np.random.Generator) -> pd.DataFrame:
    n = len(df)
    df = df.copy()
    filas = rng.choice(n, size=int(n * 0.0060), replace=False)
    df.loc[df.index[filas], "stock_cierre_unidades"] = np.nan
    filas = rng.choice(n, size=int(n * 0.0015), replace=False)
    df.loc[df.index[filas], "stock_cierre_unidades"] = -np.abs(
        rng.uniform(1, 20, size=len(filas))
    )
    duplicados = df.iloc[rng.choice(n, size=int(n * 0.0120), replace=False)]
    df = pd.concat([df, duplicados], ignore_index=True)
    return df.sample(frac=1.0, random_state=(int(cfg["proyecto"]["semilla"]) + 1) % 2**31).reset_index(drop=True)


def ensuciar_compras(df: pd.DataFrame, cfg: dict[str, Any], rng: np.random.Generator) -> pd.DataFrame:
    n = len(df)
    df = df.copy()
    filas = rng.choice(n, size=int(n * 0.0040), replace=False)
    df.loc[df.index[filas], "lead_time_dias"] = np.nan
    filas = rng.choice(n, size=int(n * 0.0020), replace=False)
    df.loc[df.index[filas], "unidades_pedido"] = -np.abs(
        rng.integers(1, 100, size=len(filas))
    )
    duplicados = df.iloc[rng.choice(n, size=int(n * 0.0100), replace=False)]
    df = pd.concat([df, duplicados], ignore_index=True)
    return df.sample(frac=1.0, random_state=(int(cfg["proyecto"]["semilla"]) + 2) % 2**31).reset_index(drop=True)


def ensuciar_dimensiones(
    dimensiones: dict[str, pd.DataFrame], rng: np.random.Generator,
) -> dict[str, pd.DataFrame]:
    salida = {nombre: tabla.copy() for nombre, tabla in dimensiones.items()}
    for nombre, cuantas in (("dim_producto", 3), ("dim_proveedor", 2)):
        tabla = salida[nombre]
        indices = rng.choice(len(tabla), size=cuantas, replace=False)
        salida[nombre] = pd.concat(
            [tabla, tabla.iloc[indices]], ignore_index=True
        ).sample(frac=1.0, random_state=7).reset_index(drop=True)
    sucursal = salida["dim_sucursal"].copy()
    indices = rng.choice(len(sucursal), size=2, replace=False)
    sucursal.loc[indices, "nombre_sucursal"] = (
        sucursal.loc[indices, "nombre_sucursal"].str.strip() + "  "
    )
    salida["dim_sucursal"] = sucursal
    return salida
