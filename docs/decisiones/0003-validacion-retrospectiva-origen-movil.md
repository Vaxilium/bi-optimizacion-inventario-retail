# ADR 0003: Validación retrospectiva con origen móvil y sin fuga de datos

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

Comparar modelos de pronóstico con una única partición train/test suele ser frágil:
el resultado depende de qué periodo cayó en la prueba. Además, las estadísticas móviles
y los rezagos son fuente típica de fuga de información (usar datos del futuro).

## Decisión

- Backtesting **rolling-origin**: varios orígenes consecutivos, horizonte fijo de 28 días,
  ventana de entrenamiento móvil. Cada origen reentrena todos los modelos.
- Todas las variables predictoras (rezagos, medias móviles, calendario) se calculan
  estrictamente con datos hasta el día anterior al origen (se valida con una prueba que
  verifica que el pronóstico de las primeras k horas no cambia al alterar el futuro).
- La selección de modelo se hace **por segmento ABC-XYZ**, no globalmente: la demanda
  intermitente exige Croston/SBA, mientras que la demanda alta y estable admite
  gradiente boosting con variables de calendario.

## Consecuencias

- Resultados más estables y creíbles; el error reportado refleja desempeño fuera de muestra.
- Mayor costo computacional por reentrenamiento repetido; se acota con una muestra
  estratificada de series y un modo `--rapido` para CI.
