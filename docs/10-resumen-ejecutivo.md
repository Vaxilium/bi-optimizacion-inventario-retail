# 10. Resumen ejecutivo

## Problema

La cadena pierde ventas por quiebre y, al mismo tiempo, inmoviliza capital en productos
de baja rotación. El análisis cuantifica ambos lados: **6.479.180 UM** de
margen perdido por quiebre y **22,5%** del capital en baja rotación.

## Qué se hizo

1. Se construyó una capa de datos con contratos y calidad verificable.
2. Se midió el problema y se identificaron las categorías y SKU críticos.
3. Se compararon modelos de pronóstico con backtesting rolling-origin.
4. Se simuló una política (s,S) con niveles de servicio por clase ABC.
5. Se diseñó y evaluó un piloto 4 vs 8 con diferencias en diferencias.
6. Se cuantificó el caso de negocio con escenarios y un Excel auditable.

## Hallazgos

- El pronóstico ajustado por censura mejora el WAPE semanal **8,4%**.
- La política propuesta sube el fill rate **+1,30 pp**, reduce la merma **-47,38%** y el costo total **-15,52%**, con capital prácticamente neutro (-0,22%).
- El piloto confirma un efecto de **+1,82 pp** (p = 0,002), con tendencias previas paralelas y potencia superior al 80%.
- El caso de negocio base tiene VAN de **4.275.881 UM**, TIR de **357,5%** y payback de **0,29 años**.

## Recomendación

Escalar por olas, comenzando por las 4 sucursales del piloto y sumando 4 por ola.
Mantener el tablero semanal, revisar parámetros mensualmente y no avanzar si la calidad
de datos o el fill rate salen de tolerancia.

## Próximos pasos

- Mantener la suite de pruebas y el CI en cada cambio.
- Publicar el repositorio y el sitio en GitHub Pages.
- Reemplazar los datos sintéticos por extractos reales en un entorno controlado.
- Revisar el caso de negocio con Finanzas y Abastecimiento antes de comprometer el capex.
