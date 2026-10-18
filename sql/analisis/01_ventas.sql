-- Evolucion mensual de ventas, margen y estacionalidad.
CREATE OR REPLACE VIEW an_ventas_mensual AS
WITH mensual AS (
    SELECT
        anio,
        mes,
        SUM(unidades) AS unidades,
        SUM(ventas) AS ventas,
        SUM(margen) AS margen,
        SUM(costo) AS costo,
        SUM(merma_valorizada) AS merma_valorizada,
        AVG(stock_promedio_valorizado) AS stock_promedio
    FROM mart_kpi_mensual
    GROUP BY 1, 2
)
SELECT
    anio,
    mes,
    ROUND(ventas, 2) AS ventas,
    ROUND(unidades, 0) AS unidades,
    ROUND(margen, 2) AS margen,
    ROUND(margen / NULLIF(ventas, 0), 4) AS margen_pct,
    ROUND(costo, 2) AS costo,
    ROUND(merma_valorizada, 2) AS merma_valorizada,
    ROUND(stock_promedio, 2) AS stock_promedio,
    ROUND(ventas / NULLIF(LAG(ventas) OVER (ORDER BY anio, mes), 0) - 1, 4) AS var_ventas_mes_previo,
    ROUND(ventas / NULLIF(SUM(ventas) OVER (PARTITION BY anio), 0), 4) AS share_anual,
    ROUND(AVG(ventas) OVER (PARTITION BY mes) / NULLIF(AVG(ventas) OVER (), 0), 3) AS indice_estacional
FROM mensual;

SELECT * FROM an_ventas_mensual ORDER BY anio, mes;
