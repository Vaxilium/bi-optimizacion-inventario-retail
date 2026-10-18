-- Mart SKU: rotacion, cobertura, GMROI, merma y perdida estimada por quiebre.

CREATE OR REPLACE VIEW mart_sku_resumen AS
WITH ventas AS (
    SELECT
        producto_id,
        SUM(venta_unidades) AS unidades,
        SUM(venta_valorizada) AS ventas,
        SUM(margen_bruto) AS margen,
        SUM(costo_total) AS costo,
        AVG(precio_unitario) AS precio_promedio,
        COUNT(*) FILTER (WHERE indicador_quiebre) AS dias_quiebre,
        COUNT(*) FILTER (WHERE venta_unidades > 0 OR indicador_quiebre) AS dias_con_demanda,
        COUNT(*) FILTER (WHERE venta_unidades > 0 AND NOT indicador_quiebre) AS dias_normales,
        SUM(venta_unidades) FILTER (WHERE venta_unidades > 0 AND NOT indicador_quiebre) AS unidades_normales,
        SUM(margen_bruto) FILTER (WHERE venta_unidades > 0 AND NOT indicador_quiebre) AS margen_normal,
        COUNT(*) FILTER (WHERE en_promocion) AS dias_en_promocion
    FROM nucleo_hechos_ventas
    GROUP BY 1
), inventario AS (
    SELECT
        producto_id,
        SUM(stock_valorizado) / COUNT(DISTINCT fecha) AS stock_promedio_valorizado,
        SUM(stock_cierre_unidades) / COUNT(DISTINCT fecha) AS stock_promedio_unidades,
        SUM(merma_valorizada) AS merma_valorizada,
        SUM(merma_unidades) AS merma_unidades
    FROM nucleo_hechos_inventario
    GROUP BY 1
)
SELECT
    p.producto_id, p.nombre_producto, p.categoria, p.subcategoria, p.marca,
    p.perecedero, p.vida_util_dias, p.costo_unitario, p.precio_lista,
    v.unidades, v.ventas, v.margen, v.costo,
    ROUND(v.margen / NULLIF(v.ventas, 0), 4) AS margen_pct,
    i.stock_promedio_valorizado, i.stock_promedio_unidades,
    i.merma_valorizada, i.merma_unidades,
    ROUND(i.merma_valorizada / NULLIF(v.ventas + i.merma_valorizada, 0), 4) AS merma_pct,
    v.dias_quiebre, v.dias_con_demanda, v.dias_normales, v.dias_en_promocion,
    ROUND(v.dias_quiebre / NULLIF(v.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(v.unidades_normales / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0) AS unidades_perdidas_estimadas,
    ROUND(v.margen_normal / NULLIF(v.dias_normales, 0) * v.dias_quiebre, 0) AS margen_perdido_estimado,
    ROUND((v.costo / 2.0) / NULLIF(i.stock_promedio_valorizado, 0), 2) AS rotacion_anual,
    ROUND(i.stock_promedio_valorizado / NULLIF(v.costo / 730.0, 0), 1) AS dias_cobertura,
    ROUND((v.margen / 2.0) / NULLIF(i.stock_promedio_valorizado, 0), 2) AS gmroi_anual
FROM ventas v
JOIN inventario i USING (producto_id)
JOIN dim_producto p USING (producto_id)
ORDER BY v.ventas DESC;
