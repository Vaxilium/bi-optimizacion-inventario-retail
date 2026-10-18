-- Capa staging: ventas. Normaliza codigos, descarta filas invalidas,
-- imputa precio desde promocion o lista, deduplica y recalcula importes.

CREATE OR REPLACE VIEW stg_ventas AS
WITH normalizada AS (
    SELECT
        CAST(v.fecha AS DATE) AS fecha,
        TRIM(v.sucursal_id) AS sucursal_id,
        UPPER(TRIM(v.producto_id)) AS producto_id,
        CAST(v.venta_unidades AS INTEGER) AS venta_unidades,
        CAST(v.precio_unitario AS DOUBLE) AS precio_unitario,
        CAST(v.en_promocion AS BOOLEAN) AS en_promocion,
        CAST(v.indicador_quiebre AS BOOLEAN) AS indicador_quiebre,
        ROW_NUMBER() OVER (
            PARTITION BY CAST(v.fecha AS DATE), TRIM(v.sucursal_id), UPPER(TRIM(v.producto_id))
            ORDER BY (v.precio_unitario IS NULL), CAST(v.precio_unitario AS DOUBLE) DESC
        ) AS orden
    FROM crudo_hechos_ventas v
    WHERE v.fecha IS NOT NULL
      AND v.sucursal_id IS NOT NULL
      AND v.producto_id IS NOT NULL
      AND v.venta_unidades IS NOT NULL
      AND CAST(v.fecha AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2025-12-31'
      AND CAST(v.venta_unidades AS INTEGER) BETWEEN 0 AND 5000
      AND UPPER(TRIM(v.producto_id)) IN (SELECT producto_id FROM stg_dim_producto)
      AND TRIM(v.sucursal_id) IN (SELECT sucursal_id FROM stg_dim_sucursal)
), con_precio AS (
    SELECT
        n.fecha,
        n.sucursal_id,
        n.producto_id,
        n.venta_unidades,
        COALESCE(n.precio_unitario, pd.precio_promocional, p.precio_lista) AS precio_unitario,
        COALESCE(n.en_promocion, FALSE) OR (pd.fecha IS NOT NULL) AS en_promocion,
        COALESCE(n.indicador_quiebre, FALSE) AS indicador_quiebre,
        p.costo_unitario
    FROM normalizada n
    JOIN stg_dim_producto p USING (producto_id)
    LEFT JOIN stg_promo_dias pd
      ON pd.producto_id = n.producto_id
     AND pd.sucursal_id = n.sucursal_id
     AND pd.fecha = n.fecha
    WHERE n.orden = 1
)
SELECT
    fecha,
    CAST(STRFTIME(fecha, '%Y%m%d') AS INTEGER) AS fecha_id,
    sucursal_id,
    producto_id,
    venta_unidades,
    ROUND(precio_unitario, 2) AS precio_unitario,
    ROUND(venta_unidades * ROUND(precio_unitario, 2), 2) AS venta_valorizada,
    ROUND(venta_unidades * costo_unitario, 2) AS costo_total,
    ROUND(venta_unidades * (ROUND(precio_unitario, 2) - costo_unitario), 2) AS margen_bruto,
    en_promocion,
    indicador_quiebre
FROM con_precio
WHERE precio_unitario BETWEEN 0.01 AND 1000;
