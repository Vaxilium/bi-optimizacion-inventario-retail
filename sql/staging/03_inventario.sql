-- Capa staging: inventario diario. Descarta stock nulo o negativo,
-- deduplica por clave y recalcula el valorizado con el costo del maestro.

CREATE OR REPLACE VIEW stg_inventario AS
WITH normalizada AS (
    SELECT
        CAST(fecha AS DATE) AS fecha,
        TRIM(sucursal_id) AS sucursal_id,
        UPPER(TRIM(producto_id)) AS producto_id,
        CAST(stock_cierre_unidades AS DOUBLE) AS stock_cierre_unidades,
        CAST(merma_unidades AS DOUBLE) AS merma_unidades,
        ROW_NUMBER() OVER (
            PARTITION BY CAST(fecha AS DATE), TRIM(sucursal_id), UPPER(TRIM(producto_id))
            ORDER BY CAST(stock_cierre_unidades AS DOUBLE) DESC
        ) AS orden
    FROM crudo_hechos_inventario
    WHERE fecha IS NOT NULL
      AND sucursal_id IS NOT NULL
      AND producto_id IS NOT NULL
      AND stock_cierre_unidades IS NOT NULL
      AND CAST(fecha AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2025-12-31'
      AND CAST(stock_cierre_unidades AS DOUBLE) >= 0
      AND UPPER(TRIM(producto_id)) IN (SELECT producto_id FROM stg_dim_producto)
      AND TRIM(sucursal_id) IN (SELECT sucursal_id FROM stg_dim_sucursal)
)
SELECT
    n.fecha,
    CAST(STRFTIME(n.fecha, '%Y%m%d') AS INTEGER) AS fecha_id,
    n.sucursal_id,
    n.producto_id,
    ROUND(n.stock_cierre_unidades, 2) AS stock_cierre_unidades,
    ROUND(n.stock_cierre_unidades * p.costo_unitario, 2) AS stock_valorizado,
    ROUND(GREATEST(COALESCE(n.merma_unidades, 0), 0), 2) AS merma_unidades,
    ROUND(GREATEST(COALESCE(n.merma_unidades, 0), 0) * p.costo_unitario, 2) AS merma_valorizada
FROM normalizada n
JOIN stg_dim_producto p USING (producto_id)
WHERE n.orden = 1;
