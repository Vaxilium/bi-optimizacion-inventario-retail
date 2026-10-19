# Optimización de inventario y pronóstico de demanda

**Supermercados Horizonte Sur** · portafolio de analítica con datos sintéticos · 2024-2025

Este proyecto recorre el ciclo completo de una iniciativa de abastecimiento: medir las
ventas perdidas, mejorar el pronóstico, rediseñar la política de reposición, validar el
cambio con un piloto controlado y cuantificar el caso de negocio.

| Indicador | Resultado |
|---|---:|
| Ventas analizadas (2 años) | 228.064.080 UM |
| Fill rate histórico | 91,3% |
| Margen perdido por quiebre | 6.479.180 UM |
| Mejora semanal del pronóstico | 8,4% |
| Fill rate con la política propuesta | 94,1% |
| Reducción de merma | -47,38% |
| Efecto del piloto (DiD) | +1,82 pp |
| VAN base del caso de negocio | 4.275.881 UM |

> **Datos sintéticos.** No corresponden a una empresa real. La verdad oculta de demanda
> se usa solo para evaluar pronósticos y políticas, nunca para entrenar modelos.

## Recorrido sugerido

1. [Marco del proyecto](01-marco-del-proyecto.md)
2. [Datos sintéticos](02-datos.md)
3. [Capa de datos](03-capa-de-datos.md)
4. [Análisis exploratorio](04-analisis.md)
5. [Pronóstico](05-pronostico.md)
6. [Optimización de inventario](06-inventario.md)
7. [Piloto](07-piloto.md)
8. [Caso de negocio](08-caso-negocio.md)
9. [Plan de implementación](09-implementacion/plan-de-implementacion.md)
10. [Resumen ejecutivo](10-resumen-ejecutivo.md)
11. [Tablero interactivo](tablero.html)

## Reproducir

```bash
make instalar
make todo
make sitio
```

Si no tienes `make`, el mismo pipeline se ejecuta con `python3 tareas.py todo` y
`python3 tareas.py sitio`. La semilla maestra y todos los parámetros viven en
`config/parametros.yaml`.
