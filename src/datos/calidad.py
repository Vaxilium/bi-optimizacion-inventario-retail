"""Bitacora de calidad: detecta defectos en la capa cruda y documenta la regla aplicada.

Cada regla se cuenta sobre la tabla cruda completa. Las filas afectadas totales
se calculan como la union (OR) de las condiciones, evitando doble conteo.
"""

from __future__ import annotations

from typing import Any

import duckdb

REGLAS_VENTAS = [
    ("Duplicados de clave (fecha, sucursal, SKU)", "Se conserva una fila por clave, priorizando precio no nulo.", "rn > 1"),
    ("Códigos de producto inconsistentes", "Normalización con UPPER(TRIM()).", "producto_id IS NOT NULL AND UPPER(TRIM(producto_id)) <> producto_id"),
    ("Claves nulas", "Se descartan las filas sin fecha, sucursal o producto.", "fecha IS NULL OR sucursal_id IS NULL OR producto_id IS NULL"),
    ("Venta en unidades nula", "Se descarta la fila.", "venta_unidades IS NULL"),
    ("Precio unitario nulo", "Se imputa con precio promocional o precio de lista.", "precio_unitario IS NULL"),
    ("Cantidades negativas", "Se descartan (no se modelan devoluciones en este proyecto).", "TRY_CAST(venta_unidades AS DOUBLE) < 0"),
    ("Fechas fuera del periodo", "Se descartan fechas anteriores a 2024 o posteriores a 2025.", "TRY_CAST(fecha AS DATE) < DATE '2024-01-01' OR TRY_CAST(fecha AS DATE) > DATE '2025-12-31'"),
    ("Claves foráneas inválidas", "Se descartan filas con sucursal o producto inexistente.", "UPPER(TRIM(producto_id)) NOT IN (SELECT UPPER(TRIM(producto_id)) FROM crudo_dim_producto WHERE producto_id IS NOT NULL) OR TRIM(sucursal_id) NOT IN (SELECT TRIM(sucursal_id) FROM crudo_dim_sucursal WHERE sucursal_id IS NOT NULL)"),
]
REGLAS_INVENTARIO = [
    ("Duplicados de clave (fecha, sucursal, SKU)", "Se conserva una fila por clave.", "rn > 1"),
    ("Códigos de producto inconsistentes", "Normalización con UPPER(TRIM()).", "producto_id IS NOT NULL AND UPPER(TRIM(producto_id)) <> producto_id"),
    ("Stock nulo o negativo", "Se descarta la fila (stock negativo es error de sistema).", "stock_cierre_unidades IS NULL OR TRY_CAST(stock_cierre_unidades AS DOUBLE) < 0"),
    ("Fechas fuera del periodo", "Se descartan fechas fuera del periodo.", "TRY_CAST(fecha AS DATE) < DATE '2024-01-01' OR TRY_CAST(fecha AS DATE) > DATE '2025-12-31'"),
    ("Claves foráneas inválidas", "Se descartan filas con sucursal o producto inexistente.", "UPPER(TRIM(producto_id)) NOT IN (SELECT UPPER(TRIM(producto_id)) FROM crudo_dim_producto WHERE producto_id IS NOT NULL) OR TRIM(sucursal_id) NOT IN (SELECT TRIM(sucursal_id) FROM crudo_dim_sucursal WHERE sucursal_id IS NOT NULL)"),
]
REGLAS_COMPRAS = [
    ("Duplicados de clave (pedido, sucursal, SKU)", "Se conserva una fila por clave.", "rn > 1"),
    ("Lead time nulo", "Se imputa con el lead time medio del proveedor.", "lead_time_dias IS NULL"),
    ("Unidades no positivas", "Se descarta la fila.", "TRY_CAST(unidades_pedido AS DOUBLE) <= 0 OR unidades_pedido IS NULL"),
    ("Fechas fuera del periodo", "Se descartan pedidos fuera del periodo.", "TRY_CAST(fecha_pedido AS DATE) < DATE '2024-01-01' OR TRY_CAST(fecha_pedido AS DATE) > DATE '2025-12-31'"),
    ("Claves foráneas inválidas", "Se descartan filas con sucursal o producto inexistente.", "UPPER(TRIM(producto_id)) NOT IN (SELECT UPPER(TRIM(producto_id)) FROM crudo_dim_producto WHERE producto_id IS NOT NULL) OR TRIM(sucursal_id) NOT IN (SELECT TRIM(sucursal_id) FROM crudo_dim_sucursal WHERE sucursal_id IS NOT NULL)"),
]
REGLAS_DIMS = [
    ("Identificadores duplicados", "Se conserva una fila por identificador.", "rn > 1"),
    ("Espacios inconsistentes en textos", "Se aplica TRIM() a los campos de texto.", "nombre <> TRIM(nombre)"),
]


def construir_bitacora(
    con: duckdb.DuckDBPyConnection, filas_limpias: dict[str, int],
) -> dict[str, Any]:
    """Ejecuta los conteos de defectos y devuelve la bitacora por tabla."""
    tablas = {
        "hechos_ventas": {
            "crudo": "crudo_hechos_ventas",
            "clave": "CAST(fecha AS DATE), TRIM(sucursal_id), UPPER(TRIM(producto_id))",
            "reglas": REGLAS_VENTAS,
        },
        "hechos_inventario": {
            "crudo": "crudo_hechos_inventario",
            "clave": "CAST(fecha AS DATE), TRIM(sucursal_id), UPPER(TRIM(producto_id))",
            "reglas": REGLAS_INVENTARIO,
        },
        "hechos_compras": {
            "crudo": "crudo_hechos_compras",
            "clave": "CAST(fecha_pedido AS DATE), TRIM(sucursal_id), UPPER(TRIM(producto_id))",
            "reglas": REGLAS_COMPRAS,
        },
        "dim_producto": {
            "crudo": "crudo_dim_producto",
            "clave": "producto_id",
            "reglas": [(REGLAS_DIMS[0][0], REGLAS_DIMS[0][1], "rn > 1"),
                       (REGLAS_DIMS[1][0], REGLAS_DIMS[1][1], "nombre_producto <> TRIM(nombre_producto)")],
        },
        "dim_sucursal": {
            "crudo": "crudo_dim_sucursal",
            "clave": "sucursal_id",
            "reglas": [(REGLAS_DIMS[0][0], REGLAS_DIMS[0][1], "rn > 1"),
                       (REGLAS_DIMS[1][0], REGLAS_DIMS[1][1], "nombre_sucursal <> TRIM(nombre_sucursal)")],
        },
        "dim_proveedor": {
            "crudo": "crudo_dim_proveedor",
            "clave": "proveedor_id",
            "reglas": [(REGLAS_DIMS[0][0], REGLAS_DIMS[0][1], "rn > 1"),
                       (REGLAS_DIMS[1][0], REGLAS_DIMS[1][1], "nombre_proveedor <> TRIM(nombre_proveedor)")],
        },
    }
    salida: dict[str, Any] = {}
    for nombre, definicion in tablas.items():
        condiciones = [f"COALESCE(({cond}), FALSE) AS c{i}" for i, (_, _, cond) in enumerate(definicion["reglas"])]
        union = " OR ".join(f"COALESCE(c{i}, FALSE)" for i in range(len(definicion["reglas"])))
        conteos = ", ".join(f"COUNT(*) FILTER (WHERE c{i}) AS n{i}" for i in range(len(definicion["reglas"])))
        consulta = f"""
            WITH base AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY {definicion['clave']} ORDER BY 1) AS rn
                FROM {definicion['crudo']}
            ), marcas AS (
                SELECT *, {', '.join(condiciones)} FROM base
            )
            SELECT COUNT(*) AS total, {conteos}, COUNT(*) FILTER (WHERE {union}) AS afectadas
            FROM marcas
        """
        fila = con.execute(consulta).fetchone()
        total, afectadas = fila[0], fila[-1]
        reglas = []
        for i, (problema, regla, _) in enumerate(definicion["reglas"]):
            reglas.append({"problema": problema, "accion": regla, "filas": int(fila[i + 1])})
        limpias = int(filas_limpias.get(nombre, 0))
        salida[nombre] = {
            "filas_crudas": int(total),
            "filas_afectadas": int(afectadas),
            "tasa_afectadas": round(afectadas / total, 4) if total else 0.0,
            "filas_limpias": limpias,
            "filas_descartadas": int(total - limpias),
            "reglas": reglas,
        }
    return salida
