-- Marts de promociones: uplift observado vs esperado y adelanto de compras.

CREATE OR REPLACE VIEW mart_promociones_efecto AS
WITH base AS (
    SELECT
        promocion_id, producto_id, sucursal_id, fecha_inicio, fecha_fin,
        tipo_promocion, descuento_pct, uplift_esperado,
        DATE_DIFF('day', fecha_inicio, fecha_fin) + 1 AS dias_promo
    FROM dim_promociones
), durante AS (
    SELECT
        b.promocion_id, SUM(v.venta_unidades) AS unidades, COUNT(*) AS dias_observados,
        SUM(v.venta_valorizada) AS ventas
    FROM base b
    JOIN nucleo_hechos_ventas v
      ON v.producto_id = b.producto_id
     AND v.sucursal_id = b.sucursal_id
     AND v.fecha BETWEEN b.fecha_inicio AND b.fecha_fin
    GROUP BY 1
), previo AS (
    SELECT
        b.promocion_id, SUM(v.venta_unidades) AS unidades_previas, COUNT(*) AS dias_previos
    FROM base b
    JOIN nucleo_hechos_ventas v
      ON v.producto_id = b.producto_id
     AND v.sucursal_id = b.sucursal_id
     AND v.fecha BETWEEN b.fecha_inicio - INTERVAL 14 DAY AND b.fecha_inicio - INTERVAL 1 DAY
    GROUP BY 1
), posterior AS (
    SELECT
        b.promocion_id, SUM(v.venta_unidades) AS unidades_post, COUNT(*) AS dias_post
    FROM base b
    JOIN nucleo_hechos_ventas v
      ON v.producto_id = b.producto_id
     AND v.sucursal_id = b.sucursal_id
     AND v.fecha BETWEEN b.fecha_fin + INTERVAL 1 DAY AND b.fecha_fin + INTERVAL 7 DAY
    GROUP BY 1
)
SELECT
    b.promocion_id, b.producto_id, p.nombre_producto, p.categoria, b.sucursal_id,
    b.tipo_promocion, b.descuento_pct, b.uplift_esperado, b.dias_promo,
    d.dias_observados, d.unidades, d.ventas,
    e.dias_previos, e.unidades_previas,
    o.dias_post, o.unidades_post,
    ROUND(d.unidades / NULLIF(d.dias_observados, 0), 2) AS unidades_por_dia,
    ROUND(e.unidades_previas / NULLIF(e.dias_previos, 0), 2) AS base_por_dia,
    ROUND((d.unidades / NULLIF(d.dias_observados, 0)) /
          NULLIF(e.unidades_previas / NULLIF(e.dias_previos, 0), 0) - 1, 4) AS uplift_real,
    ROUND((o.unidades_post / NULLIF(o.dias_post, 0)) /
          NULLIF(e.unidades_previas / NULLIF(e.dias_previos, 0), 0) - 1, 4) AS efecto_post
FROM base b
JOIN durante d USING (promocion_id)
JOIN previo e USING (promocion_id)
JOIN posterior o USING (promocion_id)
JOIN dim_producto p USING (producto_id)
WHERE d.dias_observados >= 3 AND e.dias_previos >= 7
ORDER BY b.fecha_inicio, b.promocion_id;
