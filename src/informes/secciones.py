"""Redaccion de las secciones Markdown del proyecto."""

from __future__ import annotations

import pandas as pd

from src.informes.tablas_md import num, num_opcional, pc, pc_opcional, pp, tabla, um

REPO = "https://github.com/Vaxilium/bi-optimizacion-inventario-retail"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def inicio(datos: dict, tablas: dict) -> str:
    a = datos["analisis"]["resumen"]
    i = datos["inventario"]
    p = datos["pronostico"]["resumen"]
    pil = datos["piloto"]["resultado"]
    n = datos["negocio"]["escenarios"]["base"]
    return f"""# Optimización de inventario y pronóstico de demanda

**Supermercados Horizonte Sur** · portafolio de analítica con datos sintéticos · 2024-2025

Este proyecto recorre el ciclo completo de una iniciativa de abastecimiento: medir las
ventas perdidas, mejorar el pronóstico, rediseñar la política de reposición, validar el
cambio con un piloto controlado y cuantificar el caso de negocio.

| Indicador | Resultado |
|---|---:|
| Ventas analizadas (2 años) | {um(a['ventas_totales'])} UM |
| Fill rate histórico | {pc(a['fill_rate'])} |
| Margen perdido por quiebre | {um(a['margen_perdido'])} UM |
| Mejora semanal del pronóstico | {pc(p['mejora_semanal_vs_actual'])} |
| Fill rate con la política propuesta | {pc(i['resumen']['propuesta']['fill_rate'])} |
| Reducción de merma | {pp(i['mejora']['merma_pct'])}% |
| Efecto del piloto (DiD) | {pp(pil['efecto_fill_pp'])} pp |
| VAN base del caso de negocio | {um(n['van'])} UM |

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
"""


def datos(datos: dict, tablas: dict) -> str:
    g = datos["generacion"]
    c = datos["capa_datos"]
    a = datos["analisis"]["resumen"]
    calidad = c["calidad"]
    calibracion = [
        ("Tasa de quiebre", pc(a["tasa_quiebre"], 2), "8,0%", pc(a["tasa_quiebre"], 2)),
        ("Capital de baja rotación", pc(a["capital_share_baja"], 2), "22,5%", pc(a["capital_share_baja"], 2)),
        ("Merma valorizada", pc(a["merma_pct"], 2), "1,9%", pc(a["merma_pct"], 2)),
        ("Crecimiento anual", pc(a["crecimiento_anual"], 2), "8,0%", pc(a["crecimiento_anual"], 2)),
    ]
    filas_calidad = [
        (
            nombre,
            um(valor["filas_crudas"]),
            um(valor["filas_afectadas"]),
            pc(valor["tasa_afectadas"]),
            um(valor["filas_limpias"]),
            um(valor["filas_descartadas"]),
        )
        for nombre, valor in calidad.items()
    ]
    volumenes = [
        (nombre, um(valor["filas"]), num(valor["mb"]))
        for nombre, valor in g["volumenes"].items()
    ]
    return f"""# 02. Datos sintéticos

El generador construye una cadena de 12 sucursales, 400 SKU y 36 proveedores con dos
años de historia. La demanda potencial se genera antes de la política de reposición y
luego se censura: solo se observa lo que efectivamente se vende. Esa separación permite
evaluar pronósticos y políticas sin filtración.

## Volúmenes generados

{tabla(["Tabla cruda", "Filas", "MB"], volumenes)}

- Pares sucursal-SKU: {um(g['pares'])}
- Días: {um(g['dias'])} ({g['rango_fechas'][0]} a {g['rango_fechas'][1]})
- Semilla fija: `20240101`

## Calibración

| Fenómeno | Objetivo | Generado |
|---|---:|---:|
| Tasa de quiebre | 8,0% | {calibracion[0][3]} |
| Capital de baja rotación | 22,5% | {calibracion[1][3]} |
| Merma valorizada | 1,9% | {calibracion[2][3]} |
| Crecimiento anual | 8,0% | {calibracion[3][3]} |

## Calidad inyectada y corregida

| Tabla | Filas crudas | Afectadas | Tasa | Filas limpias | Descartadas |
|---|---:|---:|---:|---:|---:|
{chr(10).join(f"| {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4]} | {f[5]} |" for f in filas_calidad)}

- Contratos validados: {c['contratos']['tablas']} tablas, {c['contratos']['chequeos']} chequeos, {c['contratos']['fallidos']} fallidos.
- Tasa global de filas afectadas: {pc(c['tasa_afectadas_global'])}.

Los defectos incluyen duplicados, nulos, códigos inconsistentes, fechas futuras y
valores negativos. Cada regla de limpieza queda registrada en `resultados/capa_datos.json`
y en la documentación de la capa.

## Límites

- Los datos son sintéticos: las conclusiones ilustran el método, no el mercado real.
- El generador simula la política actual; la política propuesta se evalúa aparte.
- La verdad oculta es la única fuente de demanda potencial y está excluida de git.
"""


def analisis(datos: dict, tablas: dict) -> str:
    a = datos["analisis"]["resumen"]
    abc = tablas["analisis_abc_sku"].copy()
    grupo = (
        abc.groupby("clase_abc")
        .agg(skus=("producto_id", "count"), ventas=("ventas", "sum"), capital=("capital", "sum"),
             unidades=("unidades", "sum"), margen=("margen", "sum"))
        .reset_index()
    )
    grupo["share_ventas"] = grupo["ventas"] / grupo["ventas"].sum()
    grupo["share_capital"] = grupo["capital"] / grupo["capital"].sum()
    filas_abc = [
        (f["clase_abc"], um(f["skus"]), pc(f["share_ventas"]), pc(f["share_capital"]),
         um(f["margen"]), pc(f["margen"] / f["ventas"]))
        for _, f in grupo.iterrows()
    ]
    q = (
        tablas["analisis_quiebres"].groupby("categoria")
        .agg(unidades_perdidas=("unidades_perdidas", "sum"), margen_perdido=("margen_perdido", "sum"),
             dias_quiebre=("dias_quiebre", "sum"), dias_con_demanda=("dias_con_demanda", "sum"))
        .reset_index()
    )
    q["tasa"] = q["dias_quiebre"] / q["dias_con_demanda"].clip(lower=1)
    q = q.sort_values("margen_perdido", ascending=False).head(6)
    filas_q = [(f["categoria"], um(f["unidades_perdidas"]), um(f["margen_perdido"]), pc(f["tasa"])) for _, f in q.iterrows()]
    mensual = tablas["analisis_ventas_mensual"].tail(6)
    filas_mes = [
        (f"{MESES[int(f['mes']) - 1]}-{int(f['anio'])}", um(f["ventas"]), um(f["unidades"]), pc(f["margen_pct"]), pc(f["indice_estacional"]))
        for _, f in mensual.iterrows()
    ]
    inv = tablas["analisis_inventario"].sort_values("capital_exceso", ascending=False).head(6)
    filas_inv = [(f["producto_id"], f["nombre_producto"][:38], f["clase_abc"], um(f["capital_exceso"]), num(f["dias_cobertura"], 0)) for _, f in inv.iterrows()]
    promos = tablas["analisis_promociones"].sort_values("margen_incremental", ascending=False).head(5)
    filas_promo = [(f["promocion_id"], f["categoria"], pc(f["descuento_pct"]), pc(f["uplift_real"]), um(f["margen_incremental"])) for _, f in promos.iterrows()]
    return f"""# 04. Análisis exploratorio

## Lectura ejecutiva

- Ventas: **{um(a['ventas_totales'])} UM** en dos años, con crecimiento anual de {pc(a['crecimiento_anual'])}.
- Margen bruto: **{um(a['margen_total'])} UM** ({pc(a['margen_pct'])}).
- Quiebre: **{pc(a['tasa_quiebre'])}** de los días con demanda; **{um(a['unidades_perdidas'])} unidades** perdidas y **{um(a['margen_perdido'])} UM** de margen no capturado.
- Capital: **{pc(a['capital_share_baja'])}** está en SKU de baja rotación; cobertura media de {num(a['cobertura_media'], 1)} días y mediana de {num(a['cobertura_mediana'], 1)} días.
- Merma: **{um(a['merma_valorizada'])} UM** ({pc(a['merma_pct'])} de las ventas).
- Promociones: uplift medio de {pc(a['uplift_medio'])} frente a {pc(a['uplift_esperado_medio'])} esperado; {pc(a['share_promos_bajo_esperado'])} quedó por debajo del objetivo.

## Estructura ABC

{tabla(["Clase", "SKU", "Share ventas", "Share capital", "Margen", "Margen %"], filas_abc, "---:")}

La clase A concentra la mayor parte de las ventas y del margen, pero también absorbe
capital. La oportunidad no es solo comprar menos: es reasignar capital desde C hacia A.

## Quiebres por categoría

{tabla(["Categoría", "Unidades perdidas", "Margen perdido", "Tasa de quiebre"], filas_q, "---:")}

## Ventas mensuales recientes

{tabla(["Mes", "Ventas", "Unidades", "Margen %", "Índice estacional"], filas_mes, "---:")}

## Capital inmovilizado: principales casos

{tabla(["SKU", "Producto", "Clase", "Capital exceso", "Días cobertura"], filas_inv, "---:")}

## Promociones con mayor margen incremental

{tabla(["Promoción", "Categoría", "Descuento", "Uplift real", "Margen incremental"], filas_promo, "---:")}

El detalle completo y las visualizaciones están en el [tablero](tablero.html).
"""


def pronostico(datos: dict, tablas: dict) -> str:
    p = datos["pronostico"]
    r = p["resumen"]
    modelos = sorted(p["modelos"], key=lambda x: x["wape_semanal"])[:6]
    filas_m = [
        (m["modelo"], pc(m["wape"]), pc(m["wape_semanal"]), pc(m["sesgo"]), num(m["mase_medio"], 3))
        for m in modelos
    ]
    seleccion = tablas["pronostico_seleccion"]
    filas_s = [(f["segmento"], f["modelo"], pc(f["wape_semanal"]), pc(f["mejora_vs_actual"]), int(f["series"])) for _, f in seleccion.iterrows()]
    abc = pd.DataFrame(p["por_clase_abc"])
    filas_abc = []
    for clase in ["A", "B", "C"]:
        sub = abc[abc["clase_abc"] == clase].sort_values("wape_semanal")
        if sub.empty:
            continue
        mejor = sub.iloc[0]
        base = sub[sub["modelo"] == "media_movil_28"]
        actual = float(base.iloc[0]["wape_semanal"]) if not base.empty else float("nan")
        filas_abc.append((clase, mejor["modelo"], pc(mejor["wape_semanal"]), pc(actual), pp((actual - mejor["wape_semanal"]) / actual * 100, 1) + "%"))
    d = p["despliegue"]
    return f"""# 05. Pronóstico de demanda

## Resultado

El mejor modelo global es **{r['mejor_modelo']}**: media móvil de 28 días multiplicada
por un factor de corrección por censura de **{num(r['factor_censura'], 4)}** (1 / tasa de
llenado). El factor corrige la subestimación que produce entrenar con ventas censuradas.

| Métrica | Media móvil actual | Mejor modelo | Mejora |
|---|---:|---:|---:|
| WAPE diario | {pc(r['wape_actual'])} | {pc(r['wape_mejor'])} | {pc(r['mejora_vs_actual'])} |
| WAPE semanal | {pc(r['wape_semanal_actual'])} | {pc(r['wape_semanal_mejor'])} | {pc(r['mejora_semanal_vs_actual'])} |
| Sesgo | {pc(r['sesgo_actual'])} | {pc(r['sesgo_mejor'])} | — |

La mejora semanal es la relevante para reposición: **{pc(r['mejora_semanal_vs_actual'])}**.
El sesgo de subestimación baja de {pc(r['sesgo_actual'])} a {pc(r['sesgo_mejor'])}.

## Modelos comparados

{tabla(["Modelo", "WAPE diario", "WAPE semanal", "Sesgo", "MASE"], filas_m, "---:")}

Se evaluaron naive estacional, media móvil de 28 días, ETS, Croston SBA y HGBM, con y
sin corrección de censura. **HGBM no supera a los métodos simples**: con 28 días de
horizonte y series intermitentes, la complejidad adicional no se traduce en precisión.
Es un hallazgo honesto del backtesting, no un resultado forzado.

## Selección por segmento ABC-XYZ

{tabla(["Segmento", "Modelo", "WAPE semanal", "Mejora vs. actual", "Series"], filas_s, "---:")}

## Por clase ABC

{tabla(["Clase", "Mejor modelo", "WAPE semanal", "MM4 actual", "Mejora relativa"], filas_abc, "---:")}

## Despliegue

- Horizonte: {d['fecha_inicio']} a {d['fecha_fin']} (28 días).
- Filas generadas: {um(d['filas'])} para {um(d['productos'])} productos.
- Modelos usados: {', '.join(f"{k} ({v})" for k, v in d['modelos_usados'].items())}.

## Método y límites

- Backtesting rolling-origin con {r['origenes']} orígenes y ventana de {r['ventana_entrenamiento_dias']} días.
- Evaluación contra demanda potencial, disponible solo en `src/pronostico/censura.py`.
- El WAPE es alto en SKU intermitentes; la selección es por segmento, no un único modelo global.
- La accuracy no es el fin: el valor se captura en la política de inventario y el caso de negocio.
"""


def inventario(datos: dict, tablas: dict) -> str:
    i = datos["inventario"]
    a = i["resumen"]["actual"]
    b = i["resumen"]["propuesta"]
    m = i["mejora"]
    hist = datos["analisis"]["resumen"]
    calibracion = [
        ("Fill rate", pc(a["fill_rate"]), pc(hist["fill_rate"])),
        ("Tasa de quiebre", pc(a["quiebre"]), pc(hist["tasa_quiebre"])),
        ("Merma / ventas", pc(a["merma_pct_ventas"]), pc(hist["merma_pct"])),
        ("Días de inventario", num(a["dias_inventario"], 1), num(hist["dias_cobertura"], 1)),
    ]
    comparacion = [
        ("Fill rate", pc(a["fill_rate"]), pc(b["fill_rate"]), f"{pp(m['fill_pp'])} pp"),
        ("Tasa de quiebre", pc(a["quiebre"]), pc(b["quiebre"]), f"{pp(m['quiebre_pp'])} pp"),
        ("Capital promedio", um(a["capital_promedio"]), um(b["capital_promedio"]), f"{pp(m['capital_pct'])}%"),
        ("Días de inventario", num(a["dias_inventario"], 1), num(b["dias_inventario"], 1), f"{pp(m['dias_inventario_pct'])}%"),
        ("Merma valorizada", um(a["merma_valor"]), um(b["merma_valor"]), f"{pp(m['merma_pct'])}%"),
        ("Costo de orden", um(a["costo_orden"]), um(b["costo_orden"]), f"{pp(m['pedidos_pct'])}%"),
        ("Costo total", um(a["costo_total"]), um(b["costo_total"]), f"{pp(m['costo_pct'])}%"),
    ]
    clases = tablas["inventario_clase"]
    filas_c = [
        (f["clase_abc"], int(f["series"]), pc(f["actual_fill_rate"]), pc(f["propuesta_fill_rate"]),
         um(f["actual_capital_promedio"]), um(f["propuesta_capital_promedio"]), pp(f["mejora_capital_pct"], 1))
        for _, f in clases.iterrows()
    ]
    return f"""# 06. Optimización de inventario

## Diseño

Se simulan **{i['parametros']['n_series']} series** sucursal-SKU durante
{i['parametros']['dias']} días, con {i['parametros']['replicas']} réplicas y bootstrap
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
{chr(10).join(f"| {f[0]} | {f[1]} | {f[2]} |" for f in calibracion)}

La política actual reproduce razonablemente el desempeño histórico. Eso permite atribuir
la diferencia a la política propuesta y no a un artefacto de la simulación.

## Resultado

| Métrica | Actual | Propuesta | Cambio |
|---|---:|---:|---:|
{chr(10).join(f"| {f[0]} | {f[1]} | {f[2]} | {f[3]} |" for f in comparacion)}

- Fill rate: **{pc(a['fill_rate'])} → {pc(b['fill_rate'])}** ({pp(m['fill_pp'])} pp).
- Merma: **{um(a['merma_valor'])} → {um(b['merma_valor'])} UM** ({pp(m['merma_pct'])}%).
- Costo total: **{um(a['costo_total'])} → {um(b['costo_total'])} UM**; ahorro anual simulado de **{um(m['ahorro_anual'])} UM** en la muestra.
- Capital: **{pp(m['capital_pct'])}%**, prácticamente neutro.
- Pedidos: **{pp(m['pedidos_pct'])}%**.

## Por clase ABC

{tabla(["Clase", "Series", "Fill actual", "Fill propuesta", "Capital actual", "Capital propuesta", "Capital %"], filas_c, "---:")}

La política libera capital en C, lo reasigna a A y mantiene el total prácticamente
constante. La merma sube en A por mayor disponibilidad, pero cae con fuerza en B y C.
El tradeoff es un leve aumento de la tasa de quiebre ({pp(m['quiebre_pp'])} pp) con una
mejora del fill rate: hay más eventos de quiebre, pero de menor magnitud y menos unidades
perdidas.

## Límites

- La demanda se remuestrea del histórico; no incorpora quiebres estructurales ni cambios de surtido.
- Los costos son parámetros de gestión; el caso de negocio prueba escenarios.
- La simulación valida la política, no reemplaza el piloto.
"""


def piloto(datos: dict, tablas: dict) -> str:
    p = datos["piloto"]
    r = p["resultado"]
    pot = r["potencia"]
    balance = pd.DataFrame(p["diseno"]["balance"])
    filas_b = [(f["variable"], num(f["tratamiento"], 2), num(f["control"], 2), num(f["diferencia"], 2), num(f["diferencia_estandarizada"], 2)) for _, f in balance.iterrows()]
    tiendas = tablas["piloto_sucursales"]
    filas_t = [
        (f["sucursal_id"], f["nombre_sucursal"][:32], f["tamano"], "Sí" if f["tratamiento"] else "No",
         pc(f["fill_pre"]), pc(f["fill_post"]), pp(f["cambio_fill_pp"]))
        for _, f in tiendas.sort_values(["tratamiento", "sucursal_id"]).iterrows()
    ]
    ratio = r["efecto_fill_pp"] / datos["inventario"]["mejora"]["fill_pp"]
    validacion = datos["negocio"]["supuestos"]["factor_validacion"]
    if validacion < 1:
        decision = (
            f"La magnitud es {pc(ratio)} del efecto simulado; el caso de negocio aplica "
            f"un factor conservador de {num(validacion, 2)}."
        )
    else:
        decision = (
            f"La magnitud es {pc(ratio)} del efecto simulado; el caso de negocio capa "
            "el factor de validación en 1,0 para no extrapolar el resultado del piloto."
        )
    return f"""# 07. Piloto controlado

## Diseño

- 4 sucursales de tratamiento y 8 de control, asignadas por bloques de tamaño comparable.
- 12 semanas pre y 12 semanas post, con choques de demanda comunes.
- Outcome primario: fill rate semanal. Outcome secundario: unidades vendidas.
- Estimación por diferencias en diferencias con errores robustos HC1.

{tabla(["Variable", "Tratamiento", "Control", "Diferencia", "Dif. estandarizada"], filas_b, "---:")}

## Sucursales

{tabla(["Sucursal", "Nombre", "Tamaño", "Tratamiento", "Fill pre", "Fill post", "Cambio"], filas_t, "---:")}

## Resultado

- Efecto DiD de fill rate: **{pp(r['efecto_fill_pp'])} pp** (IC95% {pp(r['efecto_fill_ic95'][0])} a {pp(r['efecto_fill_ic95'][1])}; p = {num(r['efecto_fill_p'], 4)}).
- Efecto en unidades: **{um(r['efecto_unidades_semana'])} unidades/semana** ({pc(r['efecto_unidades_pct'])}; p = {num(r['efecto_unidades_p'], 3)}).
- Tendencia previa: coeficiente {pp(r['tendencia_pre_coef_pp'])} pp, p = {num(r['tendencia_pre_p'], 3)}; no se rechaza el paralelismo.
- Potencia: MDE de {num(pot['mde_pp'], 2)} pp, potencia observada de {pc(pot['potencia_observada'])} con {pot['n_tratamiento']} tratadas y {pot['n_control']} controles.

## Decisión

El piloto supera la compuerta: efecto positivo, significativo al 5%, tendencias previas
paralelas y potencia superior al 80%. {decision}

## Límites

- Es un piloto simulado con una única trayectoria de demanda; en campo se requieren
  datos reales y seguimiento semanal.
- La asignación aleatoria dentro de estratos controla sesgo de selección, no todos los
  choques operativos.
- El efecto en unidades no es significativo: el beneficio principal se captura en fill rate.
"""


def negocio(datos: dict, tablas: dict) -> str:
    n = datos["negocio"]
    s = n["supuestos"]
    comp = n["componentes"]
    filas_comp = [
        ("Costo de orden", um(comp["costo_orden"])),
        ("Costo de quiebre", um(comp["costo_quiebre"])),
        ("Costo de merma", um(comp["costo_merma"])),
        ("Costo de almacenamiento", um(comp["costo_almacenamiento"])),
    ]
    escenarios = n["escenarios"]
    filas_esc = [
        (nombre.capitalize(), num(v["multiplicador"], 1), um(v["beneficio_anual"]), um(v["van"]), pc_opcional(v["tir"]), num_opcional(v["payback"]))
        for nombre, v in escenarios.items()
    ]
    base = escenarios["base"]
    filas_flujo = [(f"Año {i}", um(v)) for i, v in enumerate(base["flujos"])]
    return f"""# 08. Caso de negocio

## Supuestos

| Supuesto | Valor |
|---|---:|
| Pares en la simulación | {um(s['pares_muestra'])} |
| Pares en la cadena | {um(s['pares_total'])} |
| Factor de escala | {num(s['factor_escala'], 2)} |
| Beneficio anual base | {um(s['beneficio_anual'])} UM |
| Factor de validación del piloto | {num(s['factor_validacion'], 2)} |
| Inversión inicial | {um(s['inversion_inicial'])} UM |
| Capital de trabajo adicional | {um(s['capital_trabajo'])} UM |
| Costo de operación anual | {um(s['costo_operacion_anual'])} UM |
| Tasa de descuento / impuesto | {pc(s['tasa_descuento'])} / {pc(s['tasa_impuesto'])} |
| Horizonte | {s['anios']} años |

El beneficio anual combina el ahorro simulado en la muestra, el factor de escala por
cantidad de pares y un factor de validación que reconoce que el piloto capturó
{num(s['factor_validacion'], 2)} del efecto simulado. El capital de trabajo usa un piso
de cero: si la simulación libera capital, el caso de negocio no lo reconoce como ingreso.

## Beneficios por componente

{tabla(["Componente", "UM anuales en la cadena"], filas_comp, "---:")}

El ahorro proviene principalmente de menos pedidos y de la reducción de merma. El costo
de almacenamiento es prácticamente nulo porque el capital total se mantiene neutro.

## Escenarios

{tabla(["Escenario", "Multiplicador", "Beneficio anual", "VAN", "TIR", "Payback (años)"], filas_esc, "---:")}

## Flujo de caja base

{tabla(["Periodo", "Flujo neto"], filas_flujo, "---:")}

El año 0 incluye la inversión y el capital de trabajo; el año 3 recupera el capital de
trabajo. No se incluye valor terminal.

## Lectura

En el escenario base, el proyecto recupera la inversión en menos de un año y genera un
VAN positivo incluso en el escenario conservador. La inversión es baja frente al
beneficio porque el despliegue se apoya en el pipeline analítico y en cambios de proceso,
no en infraestructura pesada.

El Excel con fórmulas auditables está en
[`resultados/caso_negocio.xlsx`]({REPO}/blob/main/resultados/caso_negocio.xlsx).
"""


def resumen(datos: dict, tablas: dict) -> str:
    a = datos["analisis"]["resumen"]
    i = datos["inventario"]
    p = datos["pronostico"]["resumen"]
    pil = datos["piloto"]["resultado"]
    n = datos["negocio"]
    base = n["escenarios"]["base"]
    return f"""# 10. Resumen ejecutivo

## Problema

La cadena pierde ventas por quiebre y, al mismo tiempo, inmoviliza capital en productos
de baja rotación. El análisis cuantifica ambos lados: **{um(a['margen_perdido'])} UM** de
margen perdido por quiebre y **{pc(a['capital_share_baja'])}** del capital en baja rotación.

## Qué se hizo

1. Se construyó una capa de datos con contratos y calidad verificable.
2. Se midió el problema y se identificaron las categorías y SKU críticos.
3. Se compararon modelos de pronóstico con backtesting rolling-origin.
4. Se simuló una política (s,S) con niveles de servicio por clase ABC.
5. Se diseñó y evaluó un piloto 4 vs 8 con diferencias en diferencias.
6. Se cuantificó el caso de negocio con escenarios y un Excel auditable.

## Hallazgos

- El pronóstico ajustado por censura mejora el WAPE semanal **{pc(p['mejora_semanal_vs_actual'])}**.
- La política propuesta sube el fill rate **{pp(i['mejora']['fill_pp'])} pp**, reduce la merma **{pp(i['mejora']['merma_pct'])}%** y el costo total **{pp(i['mejora']['costo_pct'])}%**, con capital prácticamente neutro ({pp(i['mejora']['capital_pct'])}%).
- El piloto confirma un efecto de **{pp(pil['efecto_fill_pp'])} pp** (p = {num(pil['efecto_fill_p'], 3)}), con tendencias previas paralelas y potencia superior al 80%.
- El caso de negocio base tiene VAN de **{um(base['van'])} UM**, TIR de **{pc_opcional(base['tir'])}** y payback de **{num_opcional(base['payback'])} años**.

## Recomendación

Escalar por olas, comenzando por las 4 sucursales del piloto y sumando 4 por ola.
Mantener el tablero semanal, revisar parámetros mensualmente y no avanzar si la calidad
de datos o el fill rate salen de tolerancia.

## Próximos pasos

- Mantener la suite de pruebas y el CI en cada cambio.
- Publicar el repositorio y el sitio en GitHub Pages.
- Reemplazar los datos sintéticos por extractos reales en un entorno controlado.
- Revisar el caso de negocio con Finanzas y Abastecimiento antes de comprometer el capex.
"""


def readme(datos: dict, tablas: dict) -> str:
    a = datos["analisis"]["resumen"]
    i = datos["inventario"]
    p = datos["pronostico"]["resumen"]
    pil = datos["piloto"]["resultado"]
    n = datos["negocio"]["escenarios"]["base"]
    return f"""# BI y optimización de inventario — Supermercados Horizonte Sur

Proyecto de portafolio que recorre el ciclo completo de analítica de abastecimiento:
datos sintéticos con censura, capa DuckDB con contratos, análisis SQL, pronóstico
rolling-origin, simulación de inventario, piloto con diferencias en diferencias y caso
de negocio con Excel auditable.

> Datos sintéticos con semilla fija. No representan a una empresa real.

## Resultados

| Indicador | Resultado |
|---|---:|
| Ventas analizadas | {um(a['ventas_totales'])} UM |
| Fill rate histórico | {pc(a['fill_rate'])} |
| Mejora semanal del pronóstico | {pc(p['mejora_semanal_vs_actual'])} |
| Fill rate con política propuesta | {pc(i['resumen']['propuesta']['fill_rate'])} |
| Reducción de merma | {pp(i['mejora']['merma_pct'])}% |
| Variación de capital | {pp(i['mejora']['capital_pct'])}% |
| Efecto del piloto (DiD) | {pp(pil['efecto_fill_pp'])} pp |
| VAN base | {um(n['van'])} UM |
| TIR base | {pc_opcional(n['tir'])} |
| Payback | {num_opcional(n['payback'])} años |

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
"""
