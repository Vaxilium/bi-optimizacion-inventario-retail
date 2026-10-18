-- Quiebres y ventas perdidas por categoria, condicion perecedero y mes.
CREATE OR REPLACE VIEW an_quiebres AS
SELECT
    categoria,
    perecedero,
    anio,
    mes,
    ROUND(SUM(unidades), 0) AS unidades,
    ROUND(SUM(ventas), 2) AS ventas,
    SUM(dias_quiebre) AS dias_quiebre,
    SUM(dias_con_demanda) AS dias_con_demanda,
    ROUND(SUM(dias_quiebre) / NULLIF(SUM(dias_con_demanda), 0), 4) AS tasa_quiebre,
    ROUND(SUM(unidades_perdidas_estimadas), 0) AS unidades_perdidas,
    ROUND(SUM(margen_perdido_estimado), 2) AS margen_perdido
FROM mart_quiebres_producto_mes
GROUP BY 1, 2, 3, 4;

SELECT * FROM an_quiebres ORDER BY anio, mes, categoria;
