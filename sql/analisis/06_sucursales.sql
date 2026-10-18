-- Comparacion de sucursales: ventas, margen, quiebres y merma.
CREATE OR REPLACE VIEW an_sucursales AS
WITH base AS (
    SELECT
        sucursal_id,
        nombre_sucursal,
        region,
        tamano,
        SUM(ventas) AS ventas,
        SUM(margen) AS margen,
        SUM(unidades) AS unidades,
        SUM(merma_valorizada) AS merma_valorizada,
        AVG(stock_promedio_valorizado) AS capital,
        SUM(dias_quiebre) AS dias_quiebre,
        SUM(dias_con_demanda) AS dias_con_demanda,
        SUM(unidades_perdidas_estimadas) AS unidades_perdidas
    FROM mart_sucursal_mes
    GROUP BY 1, 2, 3, 4
)
SELECT
    sucursal_id,
    nombre_sucursal,
    region,
    tamano,
    ROUND(ventas, 2) AS ventas,
    ROUND(margen, 2) AS margen,
    ROUND(unidades, 0) AS unidades,
    ROUND(capital, 2) AS capital,
    ROUND(ventas / NULLIF(SUM(ventas) OVER (), 0), 4) AS share_ventas,
    ROUND(margen / NULLIF(ventas, 0), 4) AS margen_pct,
    ROUND((costo_estimado / 2.0) / NULLIF(capital, 0), 2) AS rotacion_anual,
    ROUND(dias_quiebre / NULLIF(dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(merma_valorizada / NULLIF(ventas + merma_valorizada, 0), 4) AS merma_pct,
    ROUND(unidades_perdidas, 0) AS unidades_perdidas,
    ranking_ventas
FROM (
    SELECT *,
        ROUND(ventas - margen, 2) AS costo_estimado,
        ROW_NUMBER() OVER (ORDER BY ventas DESC) AS ranking_ventas
    FROM base
)
ORDER BY ventas DESC;

SELECT * FROM an_sucursales ORDER BY ranking_ventas;
