# 09. Trazabilidad y reproducibilidad

## Cadena de valor analítica

```mermaid
flowchart LR
    P["Pregunta de negocio"] --> M["Métrica"]
    M --> T["Tabla fuente"]
    T --> C["Módulo / consulta"]
    C --> R["Resultado versionado"]
    R --> D["Documento o tablero"]
```

Cada cifra publicada debe recorrer esta cadena. Los documentos generados leen
`resultados/*.json`; no se transcriben números a mano.

## Matriz de trazabilidad

| Objetivo | Métrica principal | Fuente | Implementación | Salida | Documento |
|---|---|---|---|---|---|
| Medir ventas perdidas y capital ocioso | Fill rate, tasa de quiebre, margen perdido, capital por rotación | `nucleo_hechos_ventas`, `nucleo_hechos_inventario` | `sql/analisis/*.sql`, `src/analisis_sql/ejecutar.py` | `resultados/analisis.json` | 04. Análisis |
| Mejorar el pronóstico | WAPE diario y semanal, sesgo, MASE | Ventas censuradas + verdad oculta (solo evaluación) | `src/pronostico/*` | `resultados/pronostico.json` | 05. Pronóstico |
| Optimizar la reposición | Fill rate, capital, merma, costo total | Verdad oculta + parámetros operativos | `src/inventario/*`, `src/inventario/demanda.py` | `resultados/inventario.json` | 06. Inventario |
| Validar con evidencia | Efecto DiD, IC, p-valor, potencia, MDE | Panel simulado pre/post | `src/piloto/*` | `resultados/piloto.json` | 07. Piloto |
| Cuantificar el impacto | VAN, TIR, payback, beneficios por componente | Resultados de inventario y piloto + supuestos | `src/negocio/caso_negocio.py` | `resultados/negocio.json`, `caso_negocio.xlsx` | 08. Caso de negocio |

## Linaje de datos

| Capa | Ruta | Dueño | Regla de oro |
|---|---|---|---|
| Crudo | `datos/crudo/` | Ingesta | No se corrige; se conserva el defecto |
| Staging | `datos/staging/` | Datos / BI | Se normaliza y se registra cada descarte |
| Núcleo | `datos/nucleo/` | Datos / BI | Modelo estrella con claves y contratos |
| Marts | `datos/marts/` | Datos / BI | Agregados listos para consumo |
| Verdad oculta | `datos/verdad_oculta/` | Evaluación | Solo `censura.py` y `inventario/demanda.py` |

La demanda potencial nunca alimenta el pronóstico ni la política. El test de fuga de la
Fase 11 verifica que ningún otro módulo lea esa ruta.

## Definiciones de métricas

- **Fill rate:** unidades vendidas / (unidades vendidas + unidades perdidas estimadas).
- **Tasa de quiebre:** días-serie con quiebre / días-serie con demanda.
- **Capital promedio:** valorizado del stock de cierre, promedio del período.
- **Merma:** unidades vencidas valorizadas al costo.
- **Costo total:** orden + almacenamiento + quiebre + merma.
- **WAPE:** suma del error absoluto / suma de la demanda real.
- **DiD:** cambio del grupo tratado menos cambio del grupo control, con errores HC1.
- **VAN:** flujos netos descontados al WACC; incluye inversión y capital de trabajo.
- **TIR:** tasa que hace VAN = 0.
- **Payback:** tiempo hasta recuperar la inversión inicial.

## Reproducibilidad

- Semilla maestra en `config/parametros.yaml`; semillas específicas por fase.
- `make todo` reconstruye datos, capas, análisis, pronóstico, inventario, piloto,
  caso de negocio, informes, tablero y pruebas.
- `make rapido` reduce muestras y réplicas para CI, sin cambiar la lógica.
- Los Parquet, DuckDB y la verdad oculta están fuera de git; se regeneran.
- Los resultados agregados (`resultados/*.json`, tablas y Excel) sí se versionan para
  que los documentos sean auditables.

## Controles de cambio

1. Todo cambio de parámetros se registra en un commit con el prefijo `calibracion:`.
2. Los cambios de contrato o de esquema requieren actualizar `contratos/*.yaml` y el
   diccionario de datos.
3. Un resultado no se publica si `make pruebas` o `ruff check src` fallan.
4. Las cifras de un informe se regeneran desde los JSON; no se editan a mano.
