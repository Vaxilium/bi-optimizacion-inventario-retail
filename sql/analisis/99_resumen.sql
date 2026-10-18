-- Metricas ejecutivas del diagnostico, calculadas desde las vistas de analisis.
CREATE OR REPLACE VIEW an_resumen AS
WITH ventas AS (
    SELECT
        SUM(ventas) AS ventas_totales,
        SUM(unidades) AS unidades_totales,
        SUM(margen) AS margen_total,
        SUM(costo) AS costo_total,
        SUM(merma_valorizada) AS merma_valorizada,
        AVG(stock_promedio) AS capital_promedio
    FROM an_ventas_mensual
),
abc AS (
    SELECT
        COUNT(*) AS sku_total,
        COUNT(*) FILTER (WHERE clase_abc = 'A') AS sku_clase_a,
        SUM(ventas) FILTER (WHERE clase_abc = 'A') / NULLIF(SUM(ventas), 0) AS ventas_share_a,
        SUM(capital) FILTER (WHERE clase_abc = 'A') / NULLIF(SUM(capital), 0) AS capital_share_a,
        SUM(capital) FILTER (WHERE segmento_rotacion = 'Baja') / NULLIF(SUM(capital), 0) AS capital_share_baja,
        SUM(dias_quiebre) FILTER (WHERE clase_abc = 'A') / NULLIF(SUM(dias_con_demanda) FILTER (WHERE clase_abc = 'A'), 0) AS quiebre_a,
        SUM(dias_quiebre) FILTER (WHERE clase_abc = 'C') / NULLIF(SUM(dias_con_demanda) FILTER (WHERE clase_abc = 'C'), 0) AS quiebre_c
    FROM an_abc
),
promos AS (
    SELECT
        COUNT(*) AS promociones,
        AVG(uplift_real) AS uplift_medio,
        AVG(uplift_esperado) AS uplift_esperado_medio,
        SUM(unidades_incrementales) / NULLIF(SUM(unidades_base_esperadas), 0) AS uplift_ponderado,
        AVG(efecto_post) AS efecto_post_medio,
        COUNT(*) FILTER (WHERE uplift_real < uplift_esperado) / NULLIF(COUNT(*), 0) AS share_bajo_esperado,
        SUM(unidades_incrementales) AS unidades_incrementales,
        SUM(margen_incremental) AS margen_incremental
    FROM an_promociones
),
quiebres AS (
    SELECT
        SUM(dias_quiebre) AS dias_quiebre,
        SUM(dias_con_demanda) AS dias_con_demanda,
        SUM(unidades_perdidas) AS unidades_perdidas,
        SUM(margen_perdido) AS margen_perdido,
        SUM(margen_perdido) FILTER (WHERE perecedero) / NULLIF(SUM(margen_perdido), 0) AS share_perdido_perecedero
    FROM an_quiebres
),
inventario AS (
    SELECT
        SUM(capital_exceso) AS capital_exceso,
        SUM(capital_exceso) / NULLIF(SUM(capital), 0) AS share_capital_exceso,
        AVG(dias_cobertura) AS cobertura_media,
        MEDIAN(dias_cobertura) AS cobertura_mediana,
        SUM(capital) FILTER (WHERE diagnostico = 'Riesgo') AS capital_riesgo
    FROM an_inventario
),
sucursales AS (
    SELECT
        SUM(ventas) FILTER (WHERE ranking_ventas <= 3) / NULLIF(SUM(ventas), 0) AS share_top3,
        MAX(ventas) / NULLIF(SUM(ventas), 0) AS share_primera
    FROM an_sucursales
),
estacionalidad AS (
    SELECT
        MAX(indice_estacional) - MIN(indice_estacional) AS amplitud,
        MAX(indice_estacional) AS indice_maximo,
        MIN(indice_estacional) AS indice_minimo
    FROM (SELECT DISTINCT mes, indice_estacional FROM an_ventas_mensual)
)
SELECT
    ROUND(v.ventas_totales, 2) AS ventas_totales,
    ROUND(v.unidades_totales, 0) AS unidades_totales,
    ROUND(v.margen_total, 2) AS margen_total,
    ROUND(v.margen_total / NULLIF(v.ventas_totales, 0), 4) AS margen_pct,
    ROUND(v.costo_total / 2.0 / NULLIF(v.capital_promedio, 0), 2) AS rotacion_anual,
    ROUND(v.margen_total / 2.0 / NULLIF(v.capital_promedio, 0), 2) AS gmroi_anual,
    ROUND(v.capital_promedio / NULLIF(v.costo_total / 730.0, 0), 1) AS dias_cobertura,
    ROUND((SELECT SUM(ventas) FROM an_ventas_mensual WHERE anio = 2025)
          / NULLIF((SELECT SUM(ventas) FROM an_ventas_mensual WHERE anio = 2024), 0) - 1, 4) AS crecimiento_anual,
    a.sku_total,
    a.sku_clase_a,
    ROUND(a.ventas_share_a, 4) AS ventas_share_a,
    ROUND(a.capital_share_a, 4) AS capital_share_a,
    ROUND(a.capital_share_baja, 4) AS capital_share_baja,
    ROUND(a.quiebre_a, 4) AS quiebre_a,
    ROUND(a.quiebre_c, 4) AS quiebre_c,
    q.dias_quiebre,
    q.dias_con_demanda,
    ROUND(q.dias_quiebre / NULLIF(q.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(q.unidades_perdidas, 0) AS unidades_perdidas,
    ROUND(q.margen_perdido, 2) AS margen_perdido,
    ROUND(1 - q.unidades_perdidas / NULLIF(v.unidades_totales + q.unidades_perdidas, 0), 4) AS fill_rate,
    ROUND(q.share_perdido_perecedero, 4) AS share_perdido_perecedero,
    ROUND(v.merma_valorizada, 2) AS merma_valorizada,
    ROUND(v.merma_valorizada / NULLIF(v.ventas_totales + v.merma_valorizada, 0), 4) AS merma_pct,
    ROUND(i.capital_exceso, 2) AS capital_exceso,
    ROUND(i.share_capital_exceso, 4) AS share_capital_exceso,
    ROUND(i.cobertura_media, 1) AS cobertura_media,
    ROUND(i.cobertura_mediana, 1) AS cobertura_mediana,
    ROUND(i.capital_riesgo, 2) AS capital_riesgo,
    ROUND(p.promociones, 0) AS promociones,
    ROUND(p.uplift_medio, 4) AS uplift_medio,
    ROUND(p.uplift_esperado_medio, 4) AS uplift_esperado_medio,
    ROUND(p.uplift_ponderado, 4) AS uplift_ponderado,
    ROUND(p.efecto_post_medio, 4) AS efecto_post_medio,
    ROUND(p.share_bajo_esperado, 4) AS share_promos_bajo_esperado,
    ROUND(p.unidades_incrementales, 0) AS unidades_incrementales,
    ROUND(p.margen_incremental, 2) AS margen_incremental,
    ROUND(s.share_top3, 4) AS share_ventas_top3_sucursales,
    ROUND(s.share_primera, 4) AS share_ventas_primera_sucursal,
    ROUND(e.amplitud, 3) AS amplitud_estacional,
    ROUND(e.indice_maximo, 3) AS indice_estacional_maximo,
    ROUND(e.indice_minimo, 3) AS indice_estacional_minimo
FROM ventas v, abc a, promos p, quiebres q, inventario i, sucursales s, estacionalidad e;

SELECT * FROM an_resumen;
