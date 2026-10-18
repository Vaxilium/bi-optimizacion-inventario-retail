-- Marts de ventas, inventario y merma con metricas de servicio y capital.
-- La perdida estimada usa el promedio de unidades en dias sin quiebre por
-- dia de quiebre (estimador simple y conservador, documentado en el README).

CREATE OR REPLACE VIEW mart_kpi_mensual AS
WITH ventas AS (
    SELECT
        f.anio, f.mes,
        SUM(v.venta_unidades) AS unidades,
        SUM(v.venta_valorizada) AS ventas,
        SUM(v.margen_bruto) AS margen,
        SUM(v.costo_total) AS costo,
        COUNT(*) FILTER (WHERE v.indicador_quiebre) AS dias_quiebre,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 OR v.indicador_quiebre) AS dias_con_demanda,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS dias_normales,
        SUM(v.venta_unidades) FILTER (WHERE NOT v.indicador_quiebre) AS unidades_normales,
        SUM(v.margen_bruto) FILTER (WHERE NOT v.indicador_quiebre) AS margen_normal
    FROM nucleo_hechos_ventas v
    JOIN dim_fecha f USING (fecha)
    GROUP BY 1, 2
), inventario AS (
    SELECT
        f.anio, f.mes,
        SUM(i.stock_valorizado) / COUNT(DISTINCT i.fecha) AS stock_promedio,
        SUM(i.merma_valorizada) AS merma_valorizada
    FROM nucleo_hechos_inventario i
    JOIN dim_fecha f USING (fecha)
    GROUP BY 1, 2
), promociones AS (
    SELECT f.anio, f.mes, COUNT(DISTINCT p.promocion_id) AS promociones_activas
    FROM dim_promociones p
    JOIN dim_fecha f ON f.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
    GROUP BY 1, 2
)
SELECT
    v.anio, v.mes,
    v.unidades, v.ventas, v.margen, v.costo,
    COALESCE(i.stock_promedio, 0) AS stock_promedio_valorizado,
    COALESCE(i.merma_valorizada, 0) AS merma_valorizada,
    COALESCE(p.promociones_activas, 0) AS promociones_activas,
    v.dias_quiebre, v.dias_con_demanda,
    ROUND(v.dias_quiebre / NULLIF(v.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0) AS unidades_perdidas_estimadas,
    ROUND(v.unidades / NULLIF(v.unidades + v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0), 4) AS fill_rate_estimado,
    ROUND(v.margen_normal / NULLIF(v.unidades_normales, 0) * (v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre), 0) AS margen_perdido_estimado,
    ROUND(i.merma_valorizada / NULLIF(v.ventas + i.merma_valorizada, 0), 4) AS merma_pct,
    ROUND(v.margen / NULLIF(i.stock_promedio, 0), 2) AS gmroi_mensual,
    ROUND(v.costo / NULLIF(i.stock_promedio, 0), 2) AS rotacion_mensual,
    ROUND(i.stock_promedio / NULLIF(v.costo / 30.0, 0), 1) AS dias_cobertura
FROM ventas v
LEFT JOIN inventario i USING (anio, mes)
LEFT JOIN promociones p USING (anio, mes)
ORDER BY v.anio, v.mes;

CREATE OR REPLACE VIEW mart_sucursal_mes AS
WITH ventas AS (
    SELECT
        v.sucursal_id, f.anio, f.mes,
        SUM(v.venta_unidades) AS unidades,
        SUM(v.venta_valorizada) AS ventas,
        SUM(v.margen_bruto) AS margen,
        SUM(v.costo_total) AS costo,
        COUNT(*) FILTER (WHERE v.indicador_quiebre) AS dias_quiebre,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 OR v.indicador_quiebre) AS dias_con_demanda,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS dias_normales,
        SUM(v.venta_unidades) FILTER (WHERE NOT v.indicador_quiebre) AS unidades_normales,
        SUM(v.margen_bruto) FILTER (WHERE NOT v.indicador_quiebre) AS margen_normal
    FROM nucleo_hechos_ventas v
    JOIN dim_fecha f USING (fecha)
    GROUP BY 1, 2, 3
), inventario AS (
    SELECT
        i.sucursal_id, f.anio, f.mes,
        SUM(i.stock_valorizado) / COUNT(DISTINCT i.fecha) AS stock_promedio,
        SUM(i.merma_valorizada) AS merma_valorizada
    FROM nucleo_hechos_inventario i
    JOIN dim_fecha f USING (fecha)
    GROUP BY 1, 2, 3
)
SELECT
    v.sucursal_id, s.nombre_sucursal, s.region, s.tamano,
    v.anio, v.mes, v.unidades, v.ventas, v.margen, v.costo,
    COALESCE(i.stock_promedio, 0) AS stock_promedio_valorizado,
    COALESCE(i.merma_valorizada, 0) AS merma_valorizada,
    v.dias_quiebre, v.dias_con_demanda,
    ROUND(v.dias_quiebre / NULLIF(v.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0) AS unidades_perdidas_estimadas,
    ROUND(i.merma_valorizada / NULLIF(v.ventas + i.merma_valorizada, 0), 4) AS merma_pct,
    ROUND(i.stock_promedio / NULLIF(v.costo / 30.0, 0), 1) AS dias_cobertura
FROM ventas v
JOIN dim_sucursal s USING (sucursal_id)
LEFT JOIN inventario i USING (sucursal_id, anio, mes)
ORDER BY v.anio, v.mes, v.sucursal_id;

CREATE OR REPLACE VIEW mart_categoria_mes AS
WITH ventas AS (
    SELECT
        p.categoria, f.anio, f.mes,
        SUM(v.venta_unidades) AS unidades,
        SUM(v.venta_valorizada) AS ventas,
        SUM(v.margen_bruto) AS margen,
        SUM(v.costo_total) AS costo,
        COUNT(*) FILTER (WHERE v.indicador_quiebre) AS dias_quiebre,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 OR v.indicador_quiebre) AS dias_con_demanda,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS dias_normales,
        SUM(v.venta_unidades) FILTER (WHERE NOT v.indicador_quiebre) AS unidades_normales,
        SUM(v.margen_bruto) FILTER (WHERE NOT v.indicador_quiebre) AS margen_normal
    FROM nucleo_hechos_ventas v
    JOIN dim_fecha f USING (fecha)
    JOIN dim_producto p USING (producto_id)
    GROUP BY 1, 2, 3
), inventario AS (
    SELECT
        p.categoria, f.anio, f.mes,
        SUM(i.stock_valorizado) / COUNT(DISTINCT i.fecha) AS stock_promedio,
        SUM(i.merma_valorizada) AS merma_valorizada
    FROM nucleo_hechos_inventario i
    JOIN dim_fecha f USING (fecha)
    JOIN dim_producto p USING (producto_id)
    GROUP BY 1, 2, 3
)
SELECT
    v.categoria, v.anio, v.mes, v.unidades, v.ventas, v.margen, v.costo,
    COALESCE(i.stock_promedio, 0) AS stock_promedio_valorizado,
    COALESCE(i.merma_valorizada, 0) AS merma_valorizada,
    v.dias_quiebre, v.dias_con_demanda,
    ROUND(v.dias_quiebre / NULLIF(v.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0) AS unidades_perdidas_estimadas,
    ROUND(v.margen_normal / NULLIF(v.unidades_normales, 0) * (v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre), 0) AS margen_perdido_estimado,
    ROUND(i.merma_valorizada / NULLIF(v.ventas + i.merma_valorizada, 0), 4) AS merma_pct
FROM ventas v
LEFT JOIN inventario i USING (categoria, anio, mes)
ORDER BY v.anio, v.mes, v.ventas DESC;

CREATE OR REPLACE VIEW mart_categoria_dia AS
SELECT
    i.fecha,
    p.categoria,
    SUM(i.stock_valorizado) AS stock_valorizado,
    SUM(i.merma_valorizada) AS merma_valorizada
FROM nucleo_hechos_inventario i
JOIN dim_producto p USING (producto_id)
GROUP BY 1, 2
ORDER BY 1, 2;
