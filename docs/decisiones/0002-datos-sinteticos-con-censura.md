# ADR 0002: Datos sintéticos con censura de demanda y verdad oculta separada

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

No se dispone de datos reales de un retailer, y en cualquier caso las ventas observadas
de una cadena **no son la demanda**: cuando hay quiebre de stock, la venta registrada es
menor que la demanda real (demanda censurada). Ignorar este fenómeno sesga el pronóstico
hacia abajo justo en los productos que más quiebran.

## Decisión

1. El generador simula primero la **demanda potencial** (con estacionalidad, promociones,
   tendencia y demanda intermitente) y luego la dinámica de inventario con reposición.
2. La venta observada es `min(demanda_potencial, stock_disponible)` y se marca cada día censurado.
3. La demanda potencial y las ventas perdidas se guardan en `datos/verdad_oculta/`,
   fuera del alcance de los modelos. Solo la fase de validación las lee.
4. Una prueba automática verifica que ningún módulo de pronóstico importe la verdad oculta,
   salvo el módulo explícito de evaluación de censura.

## Consecuencias

- Es posible medir el sesgo que introduce la censura y cuantificar la mejora del pronóstico
  contra la demanda real, algo imposible con datos observacionales puros.
- El pipeline tiene una regla de disciplina de datos verificable por pruebas, que es
  exactamente el tipo de control que existe en un entorno productivo con capa semántica.
