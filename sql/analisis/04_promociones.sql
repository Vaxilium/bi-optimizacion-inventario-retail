-- Efecto de promociones sobre la demanda y efecto posterior.
CREATE OR REPLACE VIEW an_promociones AS
WITH base AS (
    SELECT
        p.*,
        ROUND(p.base_por_dia * p.dias_observados, 2) AS unidades_base_esperadas,
        ROUND(GREATEST(p.unidades - p.base_por_dia * p.dias_observados, 0), 0) AS unidades_incrementales,
        s.margen_pct
    FROM mart_promociones_efecto p
    LEFT JOIN mart_sku_resumen s USING (producto_id)
)
SELECT
    promocion_id,
    producto_id,
    nombre_producto,
    categoria,
    sucursal_id,
    tipo_promocion,
    descuento_pct,
    uplift_esperado,
    uplift_real,
    efecto_post,
    dias_observados,
    unidades,
    unidades_previas,
    unidades_post,
    unidades_base_esperadas,
    unidades_incrementales,
    ROUND(unidades_incrementales * (ventas / NULLIF(unidades, 0)), 2) AS ventas_incrementales,
    ROUND(unidades_incrementales * (ventas / NULLIF(unidades, 0)) * margen_pct, 2) AS margen_incremental
FROM base;

SELECT * FROM an_promociones ORDER BY uplift_real DESC;
