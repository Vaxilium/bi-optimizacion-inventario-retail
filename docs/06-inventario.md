# 06. Optimización de inventario

## Diseño

Se simulan **240 series** sucursal-SKU durante
365 días, con 6 réplicas y bootstrap
de bloques de cuatro semanas sobre la demanda potencial. Ambas políticas enfrentan la
misma demanda en cada réplica.

- **Actual:** revisión semanal (perecederos con mayor frecuencia), media móvil de 4
  semanas, 2,5 días de seguridad y compra por caja.
- **Propuesta:** política (s,S) con pronóstico ajustado por censura, nivel de servicio
  por clase ABC (A 97,5%, B 95%, C 92%), EOQ y restricción de capital.
- **Costos:** orden 42 UM, almacenamiento 19% anual, quiebre = margen perdido y merma al costo.

## Validación de la línea base

| Métrica | Simulación actual | Histórico |
|---|---:|---:|
| Fill rate | 92,8% | 91,3% |
| Tasa de quiebre | 8,0% | 7,9% |
| Merma / ventas | 2,1% | 1,9% |
| Días de inventario | 5,9 | 5,7 |

La política actual reproduce razonablemente el desempeño histórico. Eso permite atribuir
la diferencia a la política propuesta y no a un artefacto de la simulación.

## Resultado

| Métrica | Actual | Propuesta | Cambio |
|---|---:|---:|---:|
| Fill rate | 92,8% | 94,1% | +1,30 pp |
| Tasa de quiebre | 8,0% | 8,5% | +0,50 pp |
| Capital promedio | 72.927 | 72.770 | -0,22% |
| Días de inventario | 5,9 | 5,9 | -1,06% |
| Merma valorizada | 129.188 | 67.982 | -47,38% |
| Costo de orden | 876.659 | 772.359 | -11,90% |
| Costo total | 1.175.396 | 992.961 | -15,52% |

- Fill rate: **92,8% → 94,1%** (+1,30 pp).
- Merma: **129.188 → 67.982 UM** (-47,38%).
- Costo total: **1.175.396 → 992.961 UM**; ahorro anual simulado de **182.435 UM** en la muestra.
- Capital: **-0,22%**, prácticamente neutro.
- Pedidos: **-11,90%**.

## Por clase ABC

| Clase | Series | Fill actual | Fill propuesta | Capital actual | Capital propuesta | Capital % |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 55 | 94,3% | 95,7% | 46.542 | 52.657 | +13,1 |
| B | 65 | 92,0% | 93,0% | 13.128 | 13.123 | -0,0 |
| C | 120 | 85,6% | 87,0% | 13.257 | 6.990 | -47,3 |

La política libera capital en C, lo reasigna a A y mantiene el total prácticamente
constante. La merma sube en A por mayor disponibilidad, pero cae con fuerza en B y C.
El tradeoff es un leve aumento de la tasa de quiebre (+0,50 pp) con una
mejora del fill rate: hay más eventos de quiebre, pero de menor magnitud y menos unidades
perdidas.

## Límites

- La demanda se remuestrea del histórico; no incorpora quiebres estructurales ni cambios de surtido.
- Los costos son parámetros de gestión; el caso de negocio prueba escenarios.
- La simulación valida la política, no reemplaza el piloto.
