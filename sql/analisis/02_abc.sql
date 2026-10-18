-- Segmentacion ABC por ventas y clasificacion de rotacion por SKU.
CREATE OR REPLACE VIEW an_abc AS
WITH base AS (
    SELECT
        producto_id,
        nombre_producto,
        categoria,
        unidades,
        ventas,
        margen,
        costo,
        stock_promedio_valorizado AS capital,
        rotacion_anual,
        dias_cobertura,
        gmroi_anual,
        margen_pct,
        tasa_quiebre,
        dias_quiebre,
        dias_con_demanda,
        margen_perdido_estimado
    FROM mart_sku_resumen
),
ordenado AS (
    SELECT
        *,
        SUM(ventas) OVER (ORDER BY ventas DESC, producto_id) AS ventas_acumuladas,
        SUM(ventas) OVER () AS ventas_totales,
        SUM(capital) OVER () AS capital_total,
        MEDIAN(rotacion_anual) OVER () AS rotacion_mediana
    FROM base
)
SELECT
    producto_id,
    nombre_producto,
    categoria,
    unidades,
    ROUND(ventas, 2) AS ventas,
    ROUND(margen, 2) AS margen,
    ROUND(capital, 2) AS capital,
    ROUND(ventas / NULLIF(ventas_totales, 0), 4) AS share_ventas,
    ROUND(ventas_acumuladas / NULLIF(ventas_totales, 0), 4) AS share_ventas_acumulado,
    CASE
        WHEN ventas_acumuladas / NULLIF(ventas_totales, 0) <= 0.80 THEN 'A'
        WHEN ventas_acumuladas / NULLIF(ventas_totales, 0) <= 0.95 THEN 'B'
        ELSE 'C'
    END AS clase_abc,
    CASE WHEN rotacion_anual >= rotacion_mediana THEN 'Alta' ELSE 'Baja' END AS segmento_rotacion,
    ROUND(capital / NULLIF(capital_total, 0), 4) AS share_capital,
    rotacion_anual,
    dias_cobertura,
    gmroi_anual,
    margen_pct,
    tasa_quiebre,
    dias_quiebre,
    dias_con_demanda,
    margen_perdido_estimado
FROM ordenado;

SELECT * FROM an_abc ORDER BY ventas DESC;
