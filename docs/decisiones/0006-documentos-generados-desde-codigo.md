# ADR 0006: Documentos y README generados desde las salidas reales del pipeline

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

Es habitual que las cifras del README queden desactualizadas respecto del código, o que
se escriban hallazgos "a mano" que el análisis nunca produjo. En un portafolio esto es un
riesgo de credibilidad.

## Decisión

- Cada fase escribe sus métricas en `resultados/*.json` y sus tablas en `resultados/tablas/*.csv`.
- Un generador de informes (`src/informes/generar_informes.py`) compone los documentos
  de hallazgos (04 a 08), el resumen ejecutivo, el tablero y la sección de resultados del
  README usando esos archivos como única fuente de cifras.
- Las pruebas verifican que los documentos existan y que las cifras clave citadas
  coincidan con los JSON de resultados.

## Consecuencias

- `make todo` regenera el proyecto completo de forma autoconsistente.
- El texto narrativo es plantilla estática, pero **todo número proviene del pipeline**.
- Cambiar un parámetro y reejecutar actualiza documentos, tablero y README juntos.
