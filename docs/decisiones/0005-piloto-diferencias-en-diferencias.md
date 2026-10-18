# ADR 0005: Piloto 4 vs 8 sucursales con diferencias en diferencias

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

Antes de desplegar en 12 sucursales hay que demostrar que la mejora proviene de la nueva
política y no de la estacionalidad, de una promoción o de la suerte. Con 12 sucursales no
es viable aleatorizar a nivel de cliente ni hacer un experimento de mercado grande.

## Decisión

- Piloto de 12 semanas con **4 sucursales de tratamiento y 8 de control**, asignadas
  estratificando por tamaño y desempeño histórico (no por conveniencia).
- Estimación del efecto por **diferencias en diferencias** con regresión
  `resultado ~ tratamiento + post + tratamiento×post + controles`, errores robustos HC1.
- Verificación de **tendencias paralelas** en las 12 semanas previas.
- Cálculo ex ante de potencia y tamaño mínimo detectable; criterios de éxito definidos
  antes de mirar resultados.

## Consecuencias

- El diseño controla choques comunes (feriados, clima, economía) que un antes/después simple no controla.
- Con 4 sucursales tratadas la potencia es limitada: el piloto está diseñado para detectar
  efectos medianos-grandes sobre el fill rate y para confirmar que no hay efectos negativos.
- El escalamiento por olas usa los resultados del piloto como compuerta de decisión.
