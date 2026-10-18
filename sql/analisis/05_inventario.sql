-- Diagnostico de inventario por SKU: cobertura, rotacion, GMROI y exceso.
CREATE OR REPLACE VIEW an_inventario AS
WITH base AS (
    SELECT
        a.*,
        CASE a.clase_abc WHEN 'A' THEN 10 WHEN 'B' THEN 15 ELSE 25 END AS cobertura_objetivo,
        MEDIAN(a.dias_cobertura) OVER () AS cobertura_mediana
    FROM an_abc a
)
SELECT
    producto_id,
    nombre_producto,
    categoria,
    clase_abc,
    segmento_rotacion,
    capital,
    rotacion_anual,
    dias_cobertura,
    cobertura_objetivo,
    cobertura_mediana,
    gmroi_anual,
    tasa_quiebre,
    margen_perdido_estimado,
    ROUND(GREATEST(capital * (1 - cobertura_objetivo / NULLIF(dias_cobertura, 0)), 0), 2) AS capital_exceso,
    CASE
        WHEN dias_cobertura > cobertura_objetivo * 1.5 AND tasa_quiebre < 0.05 THEN 'Exceso'
        WHEN dias_cobertura < cobertura_objetivo * 0.5 AND tasa_quiebre >= 0.05 THEN 'Riesgo'
        ELSE 'Adecuado'
    END AS diagnostico
FROM base;

SELECT * FROM an_inventario ORDER BY capital_exceso DESC;
