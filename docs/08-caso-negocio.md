# 08. Caso de negocio

## Supuestos

| Supuesto | Valor |
|---|---:|
| Pares en la simulación | 240 |
| Pares en la cadena | 3.920 |
| Factor de escala | 16,33 |
| Beneficio anual base | 2.979.778 UM |
| Factor de validación del piloto | 1,00 |
| Inversión inicial | 500.000 UM |
| Capital de trabajo adicional | 0 UM |
| Costo de operación anual | 96.000 UM |
| Tasa de descuento / impuesto | 12,0% / 27,0% |
| Horizonte | 3 años |

El beneficio anual combina el ahorro simulado en la muestra, el factor de escala por
cantidad de pares y un factor de validación que reconoce que el piloto capturó
1,00 del efecto simulado. El capital de trabajo usa un piso
de cero: si la simulación libera capital, el caso de negocio no lo reconoce como ingreso.

## Beneficios por componente

| Componente | UM anuales en la cadena |
| ---: | ---: |
| Costo de orden | 1.703.567 |
| Costo de quiebre | 276.037 |
| Costo de merma | 999.686 |
| Costo de almacenamiento | 488 |

El ahorro proviene principalmente de menos pedidos y de la reducción de merma. El costo
de almacenamiento es prácticamente nulo porque el capital total se mantiene neutro.

## Escenarios

| Escenario | Multiplicador | Beneficio anual | VAN | TIR | Payback (años) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| Conservador | 0,6 | 1.787.867 | 2.341.433 | 212,1% | 0,49 |
| Base | 1,0 | 2.979.778 | 4.275.881 | 357,5% | 0,29 |
| Optimista | 1,4 | 4.171.689 | 6.210.328 | 499,7% | 0,21 |

## Flujo de caja base

| Periodo | Flujo neto |
| ---: | ---: |
| Año 0 | -500.000 |
| Año 1 | 1.715.110 |
| Año 2 | 2.150.158 |
| Año 3 | 2.150.158 |

El año 0 incluye la inversión y el capital de trabajo; el año 3 recupera el capital de
trabajo. No se incluye valor terminal.

## Lectura

En el escenario base, el proyecto recupera la inversión en menos de un año y genera un
VAN positivo incluso en el escenario conservador. La inversión es baja frente al
beneficio porque el despliegue se apoya en el pipeline analítico y en cambios de proceso,
no en infraestructura pesada.

El Excel con fórmulas auditables está en
[`resultados/caso_negocio.xlsx`](https://github.com/Vaxilium/bi-optimizacion-inventario-retail/blob/main/resultados/caso_negocio.xlsx).
