# BI y optimización de inventario — Supermercados Horizonte Sur

Proyecto de portafolio que recorre el ciclo completo de analítica de abastecimiento:
datos sintéticos con censura, capa DuckDB con contratos, análisis SQL, pronóstico
rolling-origin, simulación de inventario, piloto con diferencias en diferencias y caso
de negocio con Excel auditable.

> Datos sintéticos con semilla fija. No representan a una empresa real.

## Resultados

| Indicador | Resultado |
|---|---:|
| Ventas analizadas | 228.064.080 UM |
| Fill rate histórico | 91,3% |
| Mejora semanal del pronóstico | 8,4% |
| Fill rate con política propuesta | 94,1% |
| Reducción de merma | -47,38% |
| Variación de capital | -0,22% |
| Efecto del piloto (DiD) | +1,82 pp |
| VAN base | 4.275.881 UM |
| TIR base | 357,5% |
| Payback | 0,29 años |

## Inicio rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make todo
make sitio
```

`make todo` regenera datos, capas, análisis, pronóstico, inventario, piloto, caso de
negocio, informes, tablero y pruebas. `make rapido` reduce muestras para CI. Si no
tienes `make`, usa `python3 tareas.py todo` o `python3 tareas.py rapido`.

## Estructura

```text
tareas.py          ejecutor del pipeline sin necesidad de make
config/            parametros maestros y semillas
contratos/         contratos de datos YAML
sql/               analisis SQL
src/generacion/    generador sintetico con demanda potencial
src/datos/         capas, calidad y contratos
src/analisis_sql/  metricas ejecutivas
src/pronostico/    backtesting y despliegue
src/inventario/    simulacion de politicas
src/piloto/        diseno y estimacion DiD
src/negocio/       caso de negocio y Excel
src/informes/      documentos y README generados
src/tablero/       tablero HTML autocontenido
docs/              sitio MkDocs
resultados/        JSON, tablas, Excel y tablero
```

## Método

- **Datos:** verdad oculta de demanda y ventas censuradas; la verdad solo se usa en
  `src/pronostico/censura.py` y `src/inventario/demanda.py`.
- **Pronóstico:** naive, MM4, ETS, Croston SBA y HGBM, con corrección de censura.
- **Inventario:** política (s,S), bootstrap de bloques, costos de orden, holding, quiebre
  y merma; 240 series × 6 réplicas.
- **Piloto:** 4 tratadas vs 8 control, 12 + 12 semanas, DiD con HC1 y análisis de potencia.
- **Negocio:** VAN, TIR y payback con escenarios y capital de trabajo.

## Documentación

- [Sitio completo](https://vaxilium.github.io/bi-optimizacion-inventario-retail/)
- [Tablero](https://vaxilium.github.io/bi-optimizacion-inventario-retail/tablero.html)
- [Resumen ejecutivo](docs/10-resumen-ejecutivo.md)
- [Caso de negocio (Excel)](resultados/caso_negocio.xlsx)

## Autor

Franco Tilleria Centurión — Business Analyst / Analista Funcional  
[LinkedIn](https://www.linkedin.com/in/franco-tilleria-centurion) · [GitHub](https://github.com/Vaxilium)

Licencia MIT.
