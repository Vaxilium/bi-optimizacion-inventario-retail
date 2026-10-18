-- Capa staging: dimensiones limpias y deduplicadas.
-- Reglas: recortar espacios, castear tipos, eliminar duplicados por clave natural.

CREATE OR REPLACE VIEW stg_dim_proveedor AS
SELECT
    proveedor_id,
    TRIM(nombre_proveedor) AS nombre_proveedor,
    TRIM(categoria_principal) AS categoria_principal,
    CAST(lead_time_medio_dias AS DOUBLE) AS lead_time_medio_dias,
    CAST(lead_time_sd_dias AS DOUBLE) AS lead_time_sd_dias,
    CAST(fiabilidad AS DOUBLE) AS fiabilidad,
    CAST(unidad_minima_pedido AS INTEGER) AS unidad_minima_pedido,
    TRIM(condicion_pago) AS condicion_pago
FROM crudo_dim_proveedor
WHERE proveedor_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY proveedor_id ORDER BY nombre_proveedor) = 1;

CREATE OR REPLACE VIEW stg_dim_producto AS
SELECT
    producto_id,
    TRIM(nombre_producto) AS nombre_producto,
    TRIM(categoria) AS categoria,
    TRIM(subcategoria) AS subcategoria,
    TRIM(marca) AS marca,
    proveedor_id,
    TRIM(contenido) AS contenido,
    CAST(perecedero AS BOOLEAN) AS perecedero,
    CAST(vida_util_dias AS INTEGER) AS vida_util_dias,
    CAST(costo_unitario AS DOUBLE) AS costo_unitario,
    CAST(precio_lista AS DOUBLE) AS precio_lista,
    TRIM(unidad_medida) AS unidad_medida
FROM crudo_dim_producto
WHERE producto_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY producto_id ORDER BY nombre_producto) = 1;

CREATE OR REPLACE VIEW stg_dim_sucursal AS
SELECT
    sucursal_id,
    TRIM(nombre_sucursal) AS nombre_sucursal,
    TRIM(ciudad) AS ciudad,
    TRIM(region) AS region,
    TRIM(tipo_tienda) AS tipo_tienda,
    TRIM(tamano) AS tamano,
    CAST(superficie_m2 AS INTEGER) AS superficie_m2,
    CAST(factor_demanda AS DOUBLE) AS factor_demanda,
    CAST(fecha_apertura AS DATE) AS fecha_apertura
FROM crudo_dim_sucursal
WHERE sucursal_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY sucursal_id ORDER BY nombre_sucursal) = 1;

CREATE OR REPLACE VIEW stg_dim_fecha AS
SELECT
    CAST(fecha AS DATE) AS fecha,
    CAST(STRFTIME(CAST(fecha AS DATE), '%Y%m%d') AS INTEGER) AS fecha_id,
    CAST(anio AS INTEGER) AS anio,
    CAST(mes AS INTEGER) AS mes,
    CAST(dia AS INTEGER) AS dia,
    CAST(trimestre AS INTEGER) AS trimestre,
    CAST(dia_semana AS INTEGER) AS dia_semana,
    TRIM(nombre_dia) AS nombre_dia,
    CAST(semana_iso AS INTEGER) AS semana_iso,
    CAST(es_fin_de_semana AS BOOLEAN) AS es_fin_de_semana,
    CAST(es_feriado AS BOOLEAN) AS es_feriado,
    NULLIF(TRIM(nombre_feriado), '') AS nombre_feriado,
    CAST(es_quincena AS BOOLEAN) AS es_quincena,
    TRIM(temporada) AS temporada
FROM crudo_dim_fecha
QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(fecha AS DATE) ORDER BY fecha) = 1;

CREATE OR REPLACE VIEW stg_promociones AS
SELECT
    promocion_id,
    producto_id,
    sucursal_id,
    CAST(fecha_inicio AS DATE) AS fecha_inicio,
    CAST(fecha_fin AS DATE) AS fecha_fin,
    TRIM(tipo_promocion) AS tipo_promocion,
    CAST(descuento_pct AS DOUBLE) AS descuento_pct,
    CAST(precio_promocional AS DOUBLE) AS precio_promocional,
    CAST(uplift_esperado AS DOUBLE) AS uplift_esperado
FROM crudo_promociones
WHERE fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY promocion_id, producto_id, sucursal_id
    ORDER BY fecha_inicio
) = 1;

-- Explosion de promociones a dias: permite imputar precio y marcar en_promocion.
CREATE OR REPLACE VIEW stg_promo_dias AS
SELECT
    p.producto_id,
    p.sucursal_id,
    f.fecha,
    MIN(p.precio_promocional) AS precio_promocional,
    MIN(p.promocion_id) AS promocion_id
FROM stg_promociones p
JOIN stg_dim_fecha f
  ON f.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
GROUP BY 1, 2, 3;
