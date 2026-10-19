# 04. Análisis exploratorio

## Lectura ejecutiva

- Ventas: **228.064.080 UM** en dos años, con crecimiento anual de 7,6%.
- Margen bruto: **63.923.514 UM** (28,0%).
- Quiebre: **7,9%** de los días con demanda; **4.218.274 unidades** perdidas y **6.479.180 UM** de margen no capturado.
- Capital: **22,5%** está en SKU de baja rotación; cobertura media de 38,3 días y mediana de 6,8 días.
- Merma: **4.510.173 UM** (1,9% de las ventas).
- Promociones: uplift medio de 84,5% frente a 175,7% esperado; 86,4% quedó por debajo del objetivo.

## Estructura ABC

| Clase | SKU | Share ventas | Share capital | Margen | Margen % |
| ---: | ---: | ---: | ---: | ---: | ---: |
| A | 90 | 79,9% | 69,7% | 50.560.776 | 27,7% |
| B | 107 | 15,0% | 14,5% | 9.916.669 | 28,9% |
| C | 203 | 5,0% | 15,8% | 3.446.069 | 30,0% |

La clase A concentra la mayor parte de las ventas y del margen, pero también absorbe
capital. La oportunidad no es solo comprar menos: es reasignar capital desde C hacia A.

## Quiebres por categoría

| Categoría | Unidades perdidas | Margen perdido | Tasa de quiebre |
| ---: | ---: | ---: | ---: |
| Bebidas | 1.198.090 | 1.830.410 | 10,0% |
| Congelados | 475.022 | 1.157.847 | 10,0% |
| Carnes | 225.602 | 950.995 | 9,6% |
| Abarrotes | 839.473 | 918.514 | 6,4% |
| Higiene personal | 189.610 | 375.590 | 9,6% |
| Frutas y verduras | 371.415 | 350.588 | 7,2% |

## Ventas mensuales recientes

| Mes | Ventas | Unidades | Margen % | Índice estacional |
| ---: | ---: | ---: | ---: | ---: |
| jul-2025 | 9.256.777 | 1.792.767 | 28,0% | 93,7% |
| ago-2025 | 9.525.548 | 1.859.713 | 27,7% | 96,7% |
| sep-2025 | 9.723.451 | 1.869.355 | 28,0% | 98,6% |
| oct-2025 | 9.956.673 | 1.927.683 | 28,0% | 100,4% |
| nov-2025 | 9.891.788 | 1.912.308 | 28,1% | 100,2% |
| dic-2025 | 12.903.397 | 2.447.732 | 28,5% | 131,0% |

## Capital inmovilizado: principales casos

| SKU | Producto | Clase | Capital exceso | Días cobertura |
| ---: | ---: | ---: | ---: | ---: |
| SKU-0030 | Mar Azul Arroz largo fino 900 ml | C | 5.004 | 742 |
| SKU-0129 | Monte Verde Crema corporal 90 g | C | 3.582 | 323 |
| SKU-0069 | Sol Naciente Harina sin polvo 2 kg | C | 3.052 | 176 |
| SKU-0285 | La Pradera Agua mineral 2 L | C | 2.851 | 392 |
| SKU-0354 | Horizonte Papel higiénico 1 L | C | 2.702 | 405 |
| SKU-0031 | Mar Azul Fideos spaghetti 500 g | C | 2.524 | 265 |

## Promociones con mayor margen incremental

| Promoción | Categoría | Descuento | Uplift real | Margen incremental |
| ---: | ---: | ---: | ---: | ---: |
| PRO-003720 | Bebidas | 33,0% | 117,1% | 2.108 |
| PRO-002619 | Bebidas | 33,0% | 111,1% | 1.952 |
| PRO-000584 | Congelados | 20,0% | 170,5% | 1.906 |
| PRO-002621 | Bebidas | 33,0% | 188,0% | 1.826 |
| PRO-004273 | Carnes | 10,0% | 59,6% | 1.702 |

El detalle completo y las visualizaciones están en el [tablero](tablero.html).
