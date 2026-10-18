"""Genera el documento de capa de datos (diccionario, ERD, linaje y calidad)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.comun.config import RUTA_CONTRATOS, RUTA_DOCS, RUTA_RESULTADOS
from src.comun.resultados import formato_pct

DESCRIPCIONES = {
    "fecha": "Fecha calendario del hecho o atributo.",
    "fecha_id": "Clave entera de fecha en formato AAAAMMDD.",
    "fecha_pedido": "Fecha en que se emite el pedido al proveedor.",
    "fecha_pedido_id": "Clave entera de la fecha de pedido (AAAAMMDD).",
    "fecha_recepcion": "Fecha estimada o real de recepción del pedido.",
    "sucursal_id": "Identificador de sucursal (FK a dim_sucursal).",
    "producto_id": "Identificador de SKU (FK a dim_producto).",
    "proveedor_id": "Identificador de proveedor (FK a dim_proveedor).",
    "venta_unidades": "Unidades vendidas y observadas; si hubo quiebre, está censurada.",
    "precio_unitario": "Precio efectivo del día (promocional si aplica).",
    "venta_valorizada": "Venta en unidades monetarias (unidades × precio).",
    "costo_total": "Costo de la mercadería vendida (unidades × costo unitario).",
    "margen_bruto": "Margen bruto del día (venta valorizada − costo).",
    "en_promocion": "Indica si el SKU estaba en promoción ese día en esa sucursal.",
    "indicador_quiebre": "Verdadero si la demanda superó el stock disponible (venta censurada).",
    "stock_cierre_unidades": "Stock físico al cierre del día, en unidades.",
    "stock_valorizado": "Valor del stock al costo unitario.",
    "merma_unidades": "Unidades perdidas por vencimiento o deterioro en perecederos.",
    "merma_valorizada": "Valor de la merma al costo unitario.",
    "unidades_pedido": "Unidades solicitadas al proveedor (múltiplo de caja).",
    "lead_time_dias": "Días entre el pedido y la recepción.",
    "estado": "Estado del pedido: recibido o en tránsito al cierre del periodo.",
    "unidades_recibidas": "Unidades efectivamente recibidas dentro del periodo.",
    "nombre_producto": "Nombre comercial del producto.",
    "categoria": "Categoría comercial del producto.",
    "subcategoria": "Subcategoría comercial del producto.",
    "marca": "Marca ficticia del producto.",
    "contenido": "Contenido o tamaño del envase.",
    "perecedero": "Indica si el producto es perecedero.",
    "vida_util_dias": "Vida útil en días desde la recepción.",
    "costo_unitario": "Costo unitario de compra.",
    "precio_lista": "Precio de lista sin promoción.",
    "unidad_medida": "Unidad de medida de venta.",
    "nombre_sucursal": "Nombre comercial de la sucursal.",
    "ciudad": "Ciudad ficticia de la sucursal.",
    "region": "Región comercial (Norte, Centro, Sur, Litoral).",
    "tipo_tienda": "Formato de tienda (hipermercado, supermercado, express).",
    "tamano": "Clasificación de tamaño de la sucursal.",
    "superficie_m2": "Superficie de sala de venta en metros cuadrados.",
    "factor_demanda": "Factor de escala de demanda de la sucursal.",
    "fecha_apertura": "Fecha de apertura de la sucursal.",
    "nombre_proveedor": "Razón social ficticia del proveedor.",
    "categoria_principal": "Categoría principal que abastece el proveedor.",
    "lead_time_medio_dias": "Lead time medio de entrega en días.",
    "lead_time_sd_dias": "Desviación estándar del lead time.",
    "fiabilidad": "Proporción histórica de entregas completas y a tiempo.",
    "unidad_minima_pedido": "Múltiplo mínimo de compra (caja).",
    "condicion_pago": "Condición de pago acordada.",
    "anio": "Año calendario.",
    "mes": "Mes calendario (1 a 12).",
    "dia": "Día del mes.",
    "trimestre": "Trimestre calendario.",
    "dia_semana": "Día de la semana (1 = lunes, 7 = domingo).",
    "nombre_dia": "Nombre del día de la semana.",
    "semana_iso": "Número de semana ISO.",
    "es_fin_de_semana": "Indica si la fecha cae en fin de semana.",
    "es_feriado": "Indica si la fecha es feriado.",
    "nombre_feriado": "Nombre del feriado, si aplica.",
    "es_quincena": "Indica si la fecha corresponde a día de pago quincenal.",
    "temporada": "Temporada comercial de la fecha.",
    "promocion_id": "Identificador del evento promocional.",
    "fecha_inicio": "Primer día de vigencia de la promoción.",
    "fecha_fin": "Último día de vigencia de la promoción.",
    "tipo_promocion": "Mecánica promocional aplicada.",
    "descuento_pct": "Descuento porcentual de la promoción.",
    "precio_promocional": "Precio unitario durante la promoción.",
    "uplift_esperado": "Aumento de demanda planificado por la promoción.",
}


def generar_documento_datos(capa: dict[str, Any]) -> Path:
    contratos = []
    for ruta in sorted(RUTA_CONTRATOS.glob("*.yml")):
        with open(ruta, encoding="utf-8") as archivo:
            contratos.append(yaml.safe_load(archivo))
    texto = "\n".join([
        _encabezado(capa),
        _capas_y_linaje(),
        _erd(),
        _diccionario(contratos),
        _calidad(capa["calidad"], capa["volumenes"]),
        _contratos(capa["contratos"]),
    ])
    RUTA_DOCS.mkdir(parents=True, exist_ok=True)
    ruta_salida = RUTA_DOCS / "03-capa-de-datos.md"
    ruta_salida.write_text(texto, encoding="utf-8")
    return ruta_salida


def _entero(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _encabezado(capa: dict[str, Any]) -> str:
    total = sum(v["filas"] for v in capa["volumenes"].values() if v["capa"] == "nucleo")
    return f"""# 03. Capa de datos: modelo, contratos y calidad

El pipeline implementa cuatro capas sobre DuckDB y Parquet, con contratos de datos
verificables y una bitácora de limpieza generada automáticamente en cada ejecución.

- **Filas en la capa núcleo:** {_entero(total)}
- **Tablas con contrato validado:** {capa['contratos']['tablas']} ({capa['contratos']['chequeos']} chequeos, {capa['contratos']['fallidos']} fallidos)
- **Tasa de filas afectadas por defectos inyectados:** {formato_pct(capa['tasa_afectadas_global'], 2)}

> Todas las cifras de este documento se generan desde `resultados/capa_datos.json` y
> los contratos YAML. No se escriben a mano.
"""


def _capas_y_linaje() -> str:
    return """## Capas y linaje

```mermaid
flowchart LR
    G["Generador sintético<br/>(semilla fija)"] --> C["Crudo<br/>Parquet con defectos"]
    V["Verdad oculta<br/>(demanda potencial)"] -.->|solo validación| M["Pronóstico y evaluación"]
    C --> S["Staging<br/>normaliza, deduplica, imputa"]
    S --> N["Núcleo<br/>modelo estrella"]
    N --> A["Marts<br/>KPIs y agregados"]
    N --> M
    A --> D["Análisis SQL, piloto y tablero"]
    N --> O["Optimización de inventario"]
    D --> I["Informes generados"]
    M --> I
    O --> I
    I --> R["README, resumen ejecutivo,<br/>tablero y sitio"]
```

| Capa | Contenido | Persistencia |
|---|---|---|
| Crudo | Extractos con duplicados, nulos, códigos inconsistentes y fechas futuras | `datos/crudo/` |
| Staging | Tablas limpias con reglas documentadas y trazabilidad de defectos | `datos/staging/` |
| Núcleo | Modelo en estrella: hechos de ventas, inventario y compras + dimensiones | `datos/nucleo/` |
| Marts | Agregados mensuales, por SKU, por categoría, promociones y quiebres | `datos/marts/` |
"""


def _erd() -> str:
    return """## Modelo entidad-relación

```mermaid
erDiagram
    dim_fecha ||--o{ nucleo_hechos_ventas : fecha
    dim_fecha ||--o{ nucleo_hechos_inventario : fecha
    dim_fecha ||--o{ nucleo_hechos_compras : fecha_pedido
    dim_sucursal ||--o{ nucleo_hechos_ventas : sucursal
    dim_sucursal ||--o{ nucleo_hechos_inventario : sucursal
    dim_sucursal ||--o{ nucleo_hechos_compras : sucursal
    dim_sucursal ||--o{ dim_promociones : sucursal
    dim_producto ||--o{ nucleo_hechos_ventas : producto
    dim_producto ||--o{ nucleo_hechos_inventario : producto
    dim_producto ||--o{ nucleo_hechos_compras : producto
    dim_producto ||--o{ dim_promociones : producto
    dim_proveedor ||--o{ dim_producto : abastece
    dim_proveedor ||--o{ nucleo_hechos_compras : proveedor

    dim_producto {
        varchar producto_id PK
        varchar categoria
        boolean perecedero
        int vida_util_dias
        double costo_unitario
        double precio_lista
    }
    dim_sucursal {
        varchar sucursal_id PK
        varchar region
        varchar tamano
        double factor_demanda
    }
    dim_proveedor {
        varchar proveedor_id PK
        double lead_time_medio_dias
        double lead_time_sd_dias
        int unidad_minima_pedido
    }
    dim_fecha {
        date fecha PK
        int fecha_id
        boolean es_feriado
        boolean es_quincena
    }
    dim_promociones {
        varchar promocion_id PK
        date fecha_inicio
        date fecha_fin
        double descuento_pct
    }
    nucleo_hechos_ventas {
        date fecha
        varchar sucursal_id
        varchar producto_id
        int venta_unidades
        double margen_bruto
        boolean indicador_quiebre
    }
    nucleo_hechos_inventario {
        date fecha
        varchar sucursal_id
        varchar producto_id
        double stock_valorizado
        double merma_valorizada
    }
    nucleo_hechos_compras {
        date fecha_pedido
        varchar sucursal_id
        varchar producto_id
        int unidades_pedido
        int lead_time_dias
    }
```
"""


def _diccionario(contratos: list[dict]) -> str:
    lineas = ["## Diccionario de datos", ""]
    for contrato in contratos:
        lineas.extend([
            f"### `{contrato['tabla']}`",
            "",
            f"{contrato['descripcion']}  ",
            f"**Grano:** {contrato['grano']}",
            "",
            "| Columna | Tipo | Nulo | Descripción |",
            "|---|---|---|---|",
        ])
        for columna in contrato["columnas"]:
            descripcion = DESCRIPCIONES.get(columna["nombre"], "Atributo del modelo.")
            lineas.append(
                f"| `{columna['nombre']}` | {columna['tipo']} | "
                f"{'Sí' if columna.get('nulo', True) else 'No'} | {descripcion} |"
            )
        lineas.append("")
    return "\n".join(lineas)


def _calidad(calidad: dict[str, Any], volumenes: dict[str, Any]) -> str:
    lineas = [
        "## Informe de calidad y bitácora de limpieza",
        "",
        "| Tabla | Filas crudas | Filas afectadas | Tasa | Filas limpias |",
        "|---|---:|---:|---:|---:|",
    ]
    for tabla, datos in calidad.items():
        lineas.append(
            f"| {tabla} | {_entero(datos['filas_crudas'])} | {_entero(datos['filas_afectadas'])} | "
            f"{formato_pct(datos['tasa_afectadas'], 2)} | {_entero(datos['filas_limpias'])} |"
        )
    lineas.extend(["", "### Reglas aplicadas", ""])
    lineas.append("| Tabla | Problema detectado | Regla aplicada | Filas |")
    lineas.append("|---|---|---|---:|")
    for tabla, datos in calidad.items():
        for regla in datos["reglas"]:
            lineas.append(
                f"| {tabla} | {regla['problema']} | {regla['accion']} | {_entero(regla['filas'])} |"
            )
    lineas.extend([
        "",
        "Las filas afectadas totales consideran la unión de condiciones; un mismo registro",
        "puede presentar más de un defecto. Las filas descartadas corresponden a la",
        "diferencia entre la capa cruda y la capa staging.",
        "",
    ])
    return "\n".join(lineas)


def _contratos(contratos: dict[str, Any]) -> str:
    lineas = [
        "## Resultado de los contratos",
        "",
        f"Se ejecutaron **{contratos['chequeos']}** chequeos sobre **{contratos['tablas']}** tablas. "
        f"Chequeos fallidos: **{contratos['fallidos']}**.",
        "",
        "| Tabla | Chequeo | Estado | Detalle |",
        "|---|---|---|---|",
    ]
    for chequeo in contratos["detalle"]:
        estado = "OK" if chequeo["ok"] else "FALLA"
        lineas.append(
            f"| {chequeo['tabla']} | {chequeo['chequeo']} | {estado} | {chequeo['detalle']} |"
        )
    lineas.append("")
    return "\n".join(lineas)


def guardar_resumen_capa(capa: dict[str, Any]) -> None:
    with open(RUTA_RESULTADOS / "capa_datos.json", "w", encoding="utf-8") as archivo:
        json.dump(capa, archivo, ensure_ascii=False, indent=2, default=str)
