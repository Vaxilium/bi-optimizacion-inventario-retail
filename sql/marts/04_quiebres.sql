-- Mart de quiebres y ventas perdidas estimadas por producto y mes.

CREATE OR REPLACE VIEW mart_quiebres_producto_mes AS
WITH base AS (
    SELECT
        v.producto_id, f.anio, f.mes,
        SUM(v.venta_unidades) AS unidades,
        SUM(v.venta_valorizada) AS ventas,
        COUNT(*) FILTER (WHERE v.indicador_quiebre) AS dias_quiebre,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 OR v.indicador_quiebre) AS dias_con_demanda,
        COUNT(*) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS dias_normales,
        SUM(v.venta_unidades) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS unidades_normales,
        SUM(v.margen_bruto) FILTER (WHERE v.venta_unidades > 0 AND NOT v.indicador_quiebre) AS margen_normal
    FROM nucleo_hechos_ventas v
    JOIN dim_fecha f USING (fecha)
    GROUP BY 1, 2, 3
)
SELECT
    b.producto_id, p.nombre_producto, p.categoria, p.perecedero,
    b.anio, b.mes, b.unidades, b.ventas,
    b.dias_quiebre, b.dias_con_demanda,
    ROUND(b.dias_quiebre / NULLIF(b.dias_con_demanda, 0), 4) AS tasa_quiebre,
    ROUND(b.unidades_normales / NULLIF(b.dias_normales, 0) * b.dias_quiebre, 0) AS unidades_perdidas_estimadas,
    ROUND(b.margen_normal / NULLIF(b.dias_normales, 0) * b.dias_quiebre, 0) AS margen_perdido_estimado
FROM base b
JOIN dim_producto p USING (producto_id)
ORDER BY b.anio, b.mes, b.dias_quiebre DESC;

CREATE OR REPLACE VIEW mart_ventas_sucursal_dia AS
SELECT
    v.fecha,
    v.sucursal_id,
    SUM(v.venta_unidades) AS unidades,
    SUM(v.venta_valorizada) AS ventas,
    SUM(v.margen_bruto) AS margen,
    COUNT(*) FILTER (WHERE v.indicador_quiebre) AS quiebres,
    COUNT(*) AS observaciones
FROM nucleo_hechos_ventas v
GROUP BY 1, 2
ORDER BY 1, 2;
