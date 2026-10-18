-- Capa staging: pedidos y recepciones. Imputa lead time nulo con la media
-- del proveedor, descarta cantidades no positivas y normaliza el estado.

CREATE OR REPLACE VIEW stg_compras AS
WITH normalizada AS (
    SELECT
        CAST(c.fecha_pedido AS DATE) AS fecha_pedido,
        TRIM(c.sucursal_id) AS sucursal_id,
        UPPER(TRIM(c.producto_id)) AS producto_id,
        CAST(c.unidades_pedido AS INTEGER) AS unidades_pedido,
        CAST(c.lead_time_dias AS DOUBLE) AS lead_time_dias,
        CAST(c.fecha_recepcion AS DATE) AS fecha_recepcion,
        ROW_NUMBER() OVER (
            PARTITION BY CAST(c.fecha_pedido AS DATE), TRIM(c.sucursal_id), UPPER(TRIM(c.producto_id))
            ORDER BY CAST(c.lead_time_dias AS DOUBLE) DESC
        ) AS orden
    FROM crudo_hechos_compras c
    WHERE c.fecha_pedido IS NOT NULL
      AND c.sucursal_id IS NOT NULL
      AND c.producto_id IS NOT NULL
      AND c.unidades_pedido IS NOT NULL
      AND CAST(c.fecha_pedido AS DATE) BETWEEN DATE '2024-01-01' AND DATE '2025-12-31'
      AND CAST(c.unidades_pedido AS INTEGER) > 0
      AND UPPER(TRIM(c.producto_id)) IN (SELECT producto_id FROM stg_dim_producto)
      AND TRIM(c.sucursal_id) IN (SELECT sucursal_id FROM stg_dim_sucursal)
)
SELECT
    n.fecha_pedido,
    CAST(STRFTIME(n.fecha_pedido, '%Y%m%d') AS INTEGER) AS fecha_pedido_id,
    n.sucursal_id,
    n.producto_id,
    p.proveedor_id,
    n.unidades_pedido,
    LEAST(GREATEST(CAST(ROUND(COALESCE(n.lead_time_dias, prv.lead_time_medio_dias)) AS INTEGER), 1), 40)
        AS lead_time_dias,
    COALESCE(n.fecha_recepcion, n.fecha_pedido + CAST(ROUND(COALESCE(n.lead_time_dias, prv.lead_time_medio_dias)) AS INTEGER))
        AS fecha_recepcion,
    CASE WHEN COALESCE(n.fecha_recepcion, DATE '2026-01-01') > DATE '2025-12-31'
         THEN 'en_transito' ELSE 'recibido' END AS estado,
    CASE WHEN COALESCE(n.fecha_recepcion, DATE '2026-01-01') > DATE '2025-12-31'
         THEN 0 ELSE n.unidades_pedido END AS unidades_recibidas,
    (n.lead_time_dias IS NULL) AS lead_time_imputado
FROM normalizada n
JOIN stg_dim_producto p USING (producto_id)
JOIN stg_dim_proveedor prv USING (proveedor_id)
WHERE n.orden = 1;
