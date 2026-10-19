# 07. Piloto controlado

## Diseño

- 4 sucursales de tratamiento y 8 de control, asignadas por bloques de tamaño comparable.
- 12 semanas pre y 12 semanas post, con choques de demanda comunes.
- Outcome primario: fill rate semanal. Outcome secundario: unidades vendidas.
- Estimación por diferencias en diferencias con errores robustos HC1.

| Variable | Tratamiento | Control | Diferencia | Dif. estandarizada |
| ---: | ---: | ---: | ---: | ---: |
| unidades_base | 504.025,75 | 473.499,38 | 30.526,38 | 0,22 |
| tasa_quiebre_base | 0,08 | 0,08 | 0,00 | 0,11 |
| factor_demanda | 1,09 | 1,02 | 0,07 | 0,25 |

## Sucursales

| Sucursal | Nombre | Tamaño | Tratamiento | Fill pre | Fill post | Cambio |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SUC-01 | Horizonte Puerto Claro | Mediana | No | 95,8% | 94,7% | -1,12 |
| SUC-02 | Horizonte Valle Verde | Grande | No | 96,4% | 94,1% | -2,33 |
| SUC-05 | Horizonte Alto Molino | Mediana | No | 96,2% | 94,6% | -1,59 |
| SUC-06 | Horizonte La Ribera | Metropolitana | No | 96,0% | 94,1% | -1,89 |
| SUC-07 | Horizonte Monte Sereno | Grande | No | 96,8% | 94,1% | -2,68 |
| SUC-08 | Horizonte Campo Nuevo | Grande | No | 96,1% | 94,3% | -1,81 |
| SUC-09 | Horizonte Bahía Norte | Metropolitana | No | 96,6% | 94,6% | -2,00 |
| SUC-10 | Horizonte El Mirador | Mediana | No | 97,5% | 94,2% | -3,29 |
| SUC-03 | Horizonte San Marcos | Grande | Sí | 95,7% | 96,3% | +0,63 |
| SUC-04 | Horizonte Costa Azul | Grande | Sí | 96,5% | 95,9% | -0,59 |
| SUC-11 | Horizonte Villa Esperanza | Metropolitana | Sí | 96,4% | 95,8% | -0,54 |
| SUC-12 | Horizonte Paso Real | Mediana | Sí | 96,8% | 96,2% | -0,56 |

## Resultado

- Efecto DiD de fill rate: **+1,82 pp** (IC95% +0,70 a +2,95; p = 0,0015).
- Efecto en unidades: **574 unidades/semana** (1,8%; p = 0,231).
- Tendencia previa: coeficiente -0,88 pp, p = 0,192; no se rechaza el paralelismo.
- Potencia: MDE de 1,26 pp, potencia observada de 98,1% con 4 tratadas y 8 controles.

## Decisión

El piloto supera la compuerta: efecto positivo, significativo al 5%, tendencias previas
paralelas y potencia superior al 80%. La magnitud es 140,4% del efecto simulado; el caso de negocio capa el factor de validación en 1,0 para no extrapolar el resultado del piloto.

## Límites

- Es un piloto simulado con una única trayectoria de demanda; en campo se requieren
  datos reales y seguimiento semanal.
- La asignación aleatoria dentro de estratos controla sesgo de selección, no todos los
  choques operativos.
- El efecto en unidades no es significativo: el beneficio principal se captura en fill rate.
