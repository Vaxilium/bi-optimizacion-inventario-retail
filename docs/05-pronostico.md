# 05. Pronóstico de demanda

## Resultado

El mejor modelo global es **media_movil_28_ajustada**: media móvil de 28 días multiplicada
por un factor de corrección por censura de **1,0863** (1 / tasa de
llenado). El factor corrige la subestimación que produce entrenar con ventas censuradas.

| Métrica | Media móvil actual | Mejor modelo | Mejora |
|---|---:|---:|---:|
| WAPE diario | 41,2% | 40,6% | 1,6% |
| WAPE semanal | 25,2% | 23,1% | 8,4% |
| Sesgo | 18,9% | 11,9% | — |

La mejora semanal es la relevante para reposición: **8,4%**.
El sesgo de subestimación baja de 18,9% a 11,9%.

## Modelos comparados

| Modelo | WAPE diario | WAPE semanal | Sesgo | MASE |
| ---: | ---: | ---: | ---: | ---: |
| media_movil_28_ajustada | 40,6% | 23,1% | 11,9% | 0,865 |
| ets_ajustada | 40,8% | 23,7% | 14,3% | 0,874 |
| media_movil_28_sin_censura | 41,2% | 24,9% | 15,2% | 0,864 |
| media_movil_28 | 41,2% | 25,2% | 18,9% | 0,860 |
| ets_sin_censura | 41,6% | 25,4% | 16,1% | 0,877 |
| naive_estacional | 51,7% | 26,1% | 17,3% | 1,000 |

Se evaluaron naive estacional, media móvil de 28 días, ETS, Croston SBA y HGBM, con y
sin corrección de censura. **HGBM no supera a los métodos simples**: con 28 días de
horizonte y series intermitentes, la complejidad adicional no se traduce en precisión.
Es un hallazgo honesto del backtesting, no un resultado forzado.

## Selección por segmento ABC-XYZ

| Segmento | Modelo | WAPE semanal | Mejora vs. actual | Series |
| ---: | ---: | ---: | ---: | ---: |
| A-X | media_movil_28_ajustada | 20,4% | 10,1% | 21 |
| A-Z | ets_ajustada | 41,8% | 5,9% | 1 |
| B-X | media_movil_28_ajustada | 20,5% | 9,8% | 19 |
| B-Z | ets_sin_censura | 38,0% | 4,9% | 8 |
| C-X | naive_estacional | 22,4% | 10,0% | 10 |
| C-Z | ets_ajustada | 50,0% | 4,1% | 37 |

## Por clase ABC

| Clase | Mejor modelo | WAPE semanal | MM4 actual | Mejora relativa |
| ---: | ---: | ---: | ---: | ---: |
| A | media_movil_28_ajustada | 20,9% | 23,2% | +9,7% |
| B | media_movil_28_ajustada | 23,7% | 25,6% | +7,6% |
| C | ets_ajustada | 33,6% | 35,8% | +6,0% |

## Despliegue

- Horizonte: 2026-01-01 a 2026-01-28 (28 días).
- Filas generadas: 11.200 para 400 productos.
- Modelos usados: naive_estacional (143), media_movil_28_ajustada (222), ets_ajustada (35).

## Método y límites

- Backtesting rolling-origin con 3 orígenes y ventana de 364 días.
- Evaluación contra demanda potencial, disponible solo en `src/pronostico/censura.py`.
- El WAPE es alto en SKU intermitentes; la selección es por segmento, no un único modelo global.
- La accuracy no es el fin: el valor se captura en la política de inventario y el caso de negocio.
