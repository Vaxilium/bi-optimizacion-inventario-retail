# 02. Datos sintéticos

El generador construye una cadena de 12 sucursales, 400 SKU y 36 proveedores con dos
años de historia. La demanda potencial se genera antes de la política de reposición y
luego se censura: solo se observa lo que efectivamente se vende. Esa separación permite
evaluar pronósticos y políticas sin filtración.

## Volúmenes generados

| Tabla cruda | Filas | MB |
| --- | --- | --- |
| hechos_ventas_crudo | 2.899.906 | 29,26 |
| hechos_inventario_crudo | 2.899.906 | 29,71 |
| hechos_compras_crudo | 712.907 | 5,38 |
| dim_producto_crudo | 403 | 0,01 |
| dim_sucursal_crudo | 12 | 0,00 |
| dim_proveedor_crudo | 38 | 0,00 |
| dim_fecha_crudo | 731 | 0,01 |
| promociones_crudo | 10.237 | 0,04 |

- Pares sucursal-SKU: 3.920
- Días: 731 (2024-01-01 a 2025-12-31)
- Semilla fija: `20240101`

## Calibración

| Fenómeno | Objetivo | Generado |
|---|---:|---:|
| Tasa de quiebre | 8,0% | 7,88% |
| Capital de baja rotación | 22,5% | 22,46% |
| Merma valorizada | 1,9% | 1,94% |
| Crecimiento anual | 8,0% | 7,56% |

## Calidad inyectada y corregida

| Tabla | Filas crudas | Afectadas | Tasa | Filas limpias | Descartadas |
|---|---:|---:|---:|---:|---:|
| hechos_ventas | 2.899.906 | 77.120 | 2,7% | 2.842.661 | 57.245 |
| hechos_inventario | 2.899.906 | 55.846 | 1,9% | 2.844.060 | 55.846 |
| hechos_compras | 712.907 | 11.286 | 1,6% | 704.438 | 8.469 |
| dim_producto | 403 | 3 | 0,7% | 400 | 3 |
| dim_sucursal | 12 | 2 | 16,7% | 12 | 0 |
| dim_proveedor | 38 | 2 | 5,3% | 36 | 2 |

- Contratos validados: 8 tablas, 257 chequeos, 0 fallidos.
- Tasa global de filas afectadas: 2,2%.

Los defectos incluyen duplicados, nulos, códigos inconsistentes, fechas futuras y
valores negativos. Cada regla de limpieza queda registrada en `resultados/capa_datos.json`
y en la documentación de la capa.

## Límites

- Los datos son sintéticos: las conclusiones ilustran el método, no el mercado real.
- El generador simula la política actual; la política propuesta se evalúa aparte.
- La verdad oculta es la única fuente de demanda potencial y está excluida de git.
