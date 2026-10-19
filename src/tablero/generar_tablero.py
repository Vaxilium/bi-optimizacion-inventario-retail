"""Genera el tablero HTML autocontenido con los resultados del proyecto.

Uso:
    python -m src.tablero.generar_tablero [--rapido]

Salida:
    docs/tablero.html
"""

from __future__ import annotations

import argparse
import time

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

from src.comun.config import RAIZ, cargar_parametros
from src.comun.resultados import leer_json
from src.informes.tablas_md import num, num_opcional, pc, pc_opcional, pp, um

VERDE = "#0f766e"
VERDE_CLARO = "#99f6e4"
AZUL = "#1d4ed8"
GRIS = "#94a3b8"
GRIS_OSCURO = "#475569"
ROJO = "#b91c1c"
AMBAR = "#d97706"
FONDO = "#f6f7f9"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _layout(fig: go.Figure, titulo: str, alto: int = 360, leyenda: bool = True) -> go.Figure:
    fig.update_layout(
        title={"text": titulo, "x": 0.01, "xanchor": "left", "font": {"size": 15, "color": "#111827"}},
        template="plotly_white",
        height=alto,
        margin={"l": 8, "r": 8, "t": 46, "b": 8},
        font={"family": "Inter, ui-sans-serif, system-ui, sans-serif", "size": 12, "color": GRIS_OSCURO},
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=leyenda,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "font": {"size": 11}},
        hoverlabel={"font": {"family": "Inter, ui-sans-serif, system-ui, sans-serif"}},
    )
    fig.update_xaxes(showgrid=False, linecolor="#e5e7eb", tickfont={"size": 11})
    fig.update_yaxes(gridcolor="#eef0f3", zeroline=False, tickfont={"size": 11})
    return fig


def _fig_ventas(tablas: dict) -> go.Figure:
    df = tablas["analisis_ventas_mensual"].sort_values(["anio", "mes"]).copy()
    df["etiqueta"] = [f"{MESES[m - 1]}-{str(a)[2:]}" for a, m in zip(df["anio"], df["mes"])]
    fig = go.Figure()
    fig.add_bar(
        x=df["etiqueta"], y=df["ventas"] / 1e6, name="Ventas",
        marker_color=VERDE, marker_opacity=0.85,
        hovertemplate="%{x}<br>Ventas: %{y:,.1f} M UM<extra></extra>",
    )
    fig.add_scatter(
        x=df["etiqueta"], y=df["margen_pct"] * 100, name="Margen %", yaxis="y2",
        mode="lines+markers", line={"color": AZUL, "width": 2.5}, marker={"size": 5},
        hovertemplate="%{x}<br>Margen: %{y:.1f}%<extra></extra>",
    )
    _layout(fig, "Ventas mensuales y margen")
    fig.update_yaxes(title_text="Millones UM", rangemode="tozero")
    fig.update_layout(
        yaxis2={"title": "Margen %", "overlaying": "y", "side": "right", "showgrid": False,
                "tickformat": ".0f", "range": [20, 34]},
        hovermode="x unified",
    )
    return fig


def _fig_quiebres(tablas: dict) -> go.Figure:
    df = tablas["analisis_quiebres"].groupby("categoria", as_index=False)["margen_perdido"].sum()
    df = df.sort_values("margen_perdido").tail(8)
    fig = go.Figure(go.Bar(
        x=df["margen_perdido"] / 1e6, y=df["categoria"], orientation="h",
        marker_color=ROJO, marker_opacity=0.8,
        text=[f"{v / 1e6:,.1f}" for v in df["margen_perdido"]], textposition="outside",
        hovertemplate="%{y}<br>Margen perdido: %{customdata:,.0f} UM<extra></extra>",
        customdata=df["margen_perdido"],
    ))
    _layout(fig, "Margen perdido por quiebre, por categoría", leyenda=False)
    fig.update_xaxes(title_text="Millones UM", gridcolor="#eef0f3", showgrid=True)
    fig.update_yaxes(showgrid=False)
    return fig


def _fig_pronostico(tablas: dict) -> go.Figure:
    df = tablas["pronostico_modelos"].sort_values("wape_semanal", ascending=True).copy()
    colores = [VERDE if i == 0 else AZUL if m == "media_movil_28" else GRIS for i, m in enumerate(df["modelo"])]
    fig = go.Figure(go.Bar(
        x=df["wape_semanal"] * 100, y=df["modelo"], orientation="h",
        marker_color=colores,
        text=[pc(v) for v in df["wape_semanal"]], textposition="outside",
        customdata=df[["wape", "series"]],
        hovertemplate="%{y}<br>WAPE semanal: %{x:.1f}%<br>WAPE diario: %{customdata[0]:.1%}<br>Series: %{customdata[1]:.0f}<extra></extra>",
    ))
    _layout(fig, "WAPE semanal por modelo (menor es mejor)", alto=390, leyenda=False)
    fig.update_xaxes(title_text="WAPE semanal (%)", range=[0, 42], gridcolor="#eef0f3", showgrid=True)
    fig.update_yaxes(showgrid=False, tickfont={"size": 10})
    return fig


def _fig_fill_clase(tablas: dict) -> go.Figure:
    df = tablas["inventario_clase"].copy()
    fig = go.Figure()
    for columna, nombre, color in [
        ("actual_fill_rate", "Actual", GRIS),
        ("propuesta_fill_rate", "Propuesta", VERDE),
    ]:
        fig.add_bar(
            x=df["clase_abc"], y=df[columna] * 100, name=nombre,
            marker_color=color, text=[pc(v) for v in df[columna]], textposition="outside",
            hovertemplate=f"Clase %{{x}}<br>{nombre}: %{{y:.1f}}%<extra></extra>",
        )
    _layout(fig, "Fill rate por clase ABC", alto=350)
    fig.update_yaxes(title_text="Fill rate (%)", range=[78, 101], gridcolor="#eef0f3")
    fig.update_xaxes(title_text="Clase")
    return fig


def _fig_capital_clase(tablas: dict) -> go.Figure:
    df = tablas["inventario_clase"].copy()
    fig = go.Figure()
    for columna, nombre, color in [
        ("actual_capital_promedio", "Actual", GRIS),
        ("propuesta_capital_promedio", "Propuesta", AZUL),
    ]:
        fig.add_bar(
            x=df["clase_abc"], y=df[columna], name=nombre,
            marker_color=color, text=[um(v) for v in df[columna]], textposition="outside",
            hovertemplate=f"Clase %{{x}}<br>{nombre}: %{{y:,.0f}} UM<extra></extra>",
        )
    _layout(fig, "Capital promedio por clase ABC", alto=350)
    fig.update_yaxes(title_text="UM por serie", gridcolor="#eef0f3")
    fig.update_xaxes(title_text="Clase")
    return fig


def _fig_piloto(tablas: dict) -> go.Figure:
    df = tablas["piloto_semanal"].copy()
    df["grupo"] = df["tratamiento"].map({0: "Control", 1: "Tratamiento"})
    media = df.groupby(["semana", "grupo"], as_index=False)["fill_rate"].mean()
    fig = go.Figure()
    for grupo, color in [("Control", GRIS), ("Tratamiento", VERDE)]:
        sub = media[media["grupo"] == grupo]
        fig.add_scatter(
            x=sub["semana"], y=sub["fill_rate"] * 100, name=grupo,
            mode="lines+markers", line={"color": color, "width": 2.5}, marker={"size": 5},
            hovertemplate=f"{grupo} · semana %{{x}}<br>Fill rate: %{{y:.2f}}%<extra></extra>",
        )
    fig.add_vrect(x0=0.5, x1=12.5, fillcolor=GRIS, opacity=0.06, line_width=0,
                  annotation_text="Pre", annotation_position="top left", annotation_font_size=11)
    fig.add_vrect(x0=12.5, x1=24.5, fillcolor=VERDE, opacity=0.05, line_width=0,
                  annotation_text="Post", annotation_position="top right", annotation_font_size=11)
    fig.add_vline(x=12.5, line_dash="dash", line_color=GRIS_OSCURO, line_width=1)
    _layout(fig, "Piloto: fill rate semanal por grupo", alto=380)
    fig.update_xaxes(title_text="Semana", dtick=2)
    fig.update_yaxes(title_text="Fill rate (%)", gridcolor="#eef0f3")
    return fig


def _fig_van(negocio: dict) -> go.Figure:
    escenarios = negocio["escenarios"]
    nombres = ["Conservador", "Base", "Optimista"]
    claves = ["conservador", "base", "optimista"]
    valores = [escenarios[k]["van"] / 1e6 for k in claves]
    colores = [GRIS, VERDE, GRIS]
    customdata = [[
        escenarios[k]["tir"] * 100 if escenarios[k]["tir"] is not None else float("nan"),
        escenarios[k]["payback"] if escenarios[k]["payback"] is not None else float("nan"),
    ] for k in claves]
    fig = go.Figure(go.Bar(
        x=nombres, y=valores, marker_color=colores,
        text=[f"{v:,.2f} M" for v in valores], textposition="outside",
        customdata=customdata,
        hovertemplate="%{x}<br>VAN: %{y:,.2f} M UM<br>TIR: %{customdata[0]:.1f}%<br>Payback: %{customdata[1]:.2f} años<extra></extra>",
    ))
    _layout(fig, "VAN del caso de negocio por escenario", alto=340, leyenda=False)
    fig.update_yaxes(title_text="Millones UM", rangemode="tozero", gridcolor="#eef0f3")
    fig.update_xaxes(title_text="")
    return fig


def _kpi(etiqueta: str, valor: str, detalle: str, tono: str = "verde") -> str:
    return f"""<div class="kpi {tono}"><span>{etiqueta}</span><strong>{valor}</strong><small>{detalle}</small></div>"""


def _tabla_componentes(negocio: dict) -> str:
    nombres = {
        "costo_orden": "Costo de orden",
        "costo_quiebre": "Costo de quiebre",
        "costo_merma": "Costo de merma",
        "costo_almacenamiento": "Costo de almacenamiento",
    }
    filas = "".join(
        f"<tr><td>{nombres[k]}</td><td>{um(v)}</td></tr>"
        for k, v in negocio["componentes"].items()
    )
    return f"<table><thead><tr><th>Componente</th><th>UM anuales</th></tr></thead><tbody>{filas}</tbody></table>"


def ejecutar(modo_rapido: bool = False) -> None:
    inicio = time.time()
    cargar_parametros(modo_rapido)
    datos = {n: leer_json(n) for n in ["analisis", "pronostico", "inventario", "piloto", "negocio"]}
    tablas = {
        n: pd.read_csv(RAIZ / "resultados" / "tablas" / f"{n}.csv")
        for n in [
            "analisis_ventas_mensual", "analisis_quiebres", "pronostico_modelos",
            "inventario_clase", "piloto_semanal",
        ]
    }
    a = datos["analisis"]["resumen"]
    p = datos["pronostico"]["resumen"]
    i = datos["inventario"]
    pil = datos["piloto"]["resultado"]
    neg = datos["negocio"]
    base = neg["escenarios"]["base"]

    kpis = "".join([
        _kpi("Fill rate histórico", pc(a["fill_rate"]), f"Quiebre {pc(a['tasa_quiebre'])}", "gris"),
        _kpi("Margen perdido", f"{num(a['margen_perdido'] / 1e6, 1)} M UM", "Por quiebre de stock", "rojo"),
        _kpi("Mejora del pronóstico", pp(-p["mejora_semanal_vs_actual"] * 100, 1) + "%", "WAPE semanal vs. media móvil", "azul"),
        _kpi("Fill rate propuesto", pc(i["resumen"]["propuesta"]["fill_rate"]), f"{pp(i['mejora']['fill_pp'])} pp vs. actual", "verde"),
        _kpi("Reducción de merma", pp(i["mejora"]["merma_pct"]) + "%", "Con capital prácticamente neutro", "verde"),
        _kpi("Efecto del piloto", f"{pp(pil['efecto_fill_pp'])} pp", f"DiD p = {num(pil['efecto_fill_p'], 3)}", "azul"),
        _kpi("VAN base", f"{num(base['van'] / 1e6, 2)} M UM", f"TIR {pc_opcional(base['tir'])}", "verde"),
        _kpi("Payback", f"{num_opcional(base['payback'])} años", "Inversión inicial 500.000 UM", "gris"),
    ])

    figuras = {
        "ventas": _fig_ventas(tablas),
        "quiebres": _fig_quiebres(tablas),
        "pronostico": _fig_pronostico(tablas),
        "fill": _fig_fill_clase(tablas),
        "capital": _fig_capital_clase(tablas),
        "piloto": _fig_piloto(tablas),
        "van": _fig_van(neg),
    }
    config = {"displayModeBar": False, "responsive": True}
    fragmentos = {
        clave: fig.to_html(full_html=False, include_plotlyjs=False, config=config, div_id=f"grafico-{clave}")
        for clave, fig in figuras.items()
    }

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tablero · Optimización de inventario | Supermercados Horizonte Sur</title>
<style>
:root {{ --verde:#0f766e; --azul:#1d4ed8; --rojo:#b91c1c; --gris:#64748b; --texto:#111827; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:{FONDO}; color:var(--texto);
  font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
header {{ background:linear-gradient(135deg,#0f172a 0%,#134e4a 100%); color:white; padding:38px 28px 30px; }}
.ancho {{ max-width:1180px; margin:0 auto; }}
header .ancho {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-start; }}
h1 {{ margin:0 0 8px; font-size:clamp(24px,3.4vw,38px); letter-spacing:-0.02em; }}
.sub {{ margin:0; color:#cbd5e1; max-width:720px; line-height:1.55; }}
nav {{ display:flex; gap:10px; flex-wrap:wrap; }}
nav a {{ color:white; text-decoration:none; border:1px solid #ffffff44; padding:9px 14px;
  border-radius:999px; font-size:13px; white-space:nowrap; }}
nav a:hover {{ background:#ffffff18; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 20px 40px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
.kpi {{ background:white; border:1px solid #e5e7eb; border-radius:14px; padding:16px 16px 14px;
  display:flex; flex-direction:column; gap:3px; box-shadow:0 1px 2px #0f172a08; }}
.kpi span {{ color:var(--gris); font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}
.kpi strong {{ font-size:clamp(20px,2.6vw,28px); letter-spacing:-0.03em; }}
.kpi small {{ color:var(--gris); font-size:12px; }}
.kpi.verde strong {{ color:var(--verde); }}
.kpi.azul strong {{ color:var(--azul); }}
.kpi.rojo strong {{ color:var(--rojo); }}
.kpi.gris strong {{ color:#334155; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }}
.card {{ background:white; border:1px solid #e5e7eb; border-radius:14px; padding:12px 14px 4px;
  box-shadow:0 1px 2px #0f172a08; overflow:hidden; }}
.card.ancho {{ grid-column:1 / -1; }}
.pie {{ margin:0 4px 12px; color:var(--gris); font-size:13px; line-height:1.5; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:0 4px 12px; }}
th {{ text-align:left; color:var(--gris); font-weight:600; border-bottom:1px solid #e5e7eb; padding:8px 6px; }}
td {{ padding:8px 6px; border-bottom:1px solid #f1f5f9; }}
td:last-child, th:last-child {{ text-align:right; }}
footer {{ max-width:1180px; margin:0 auto; padding:0 20px 36px; color:var(--gris); font-size:12px; }}
@media (max-width:900px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} .grid {{ grid-template-columns:1fr; }}
  header .ancho {{ flex-direction:column; }} .card.ancho {{ grid-column:auto; }} }}
@media (max-width:520px) {{ .kpis {{ grid-template-columns:1fr; }} main {{ padding:16px 12px 28px; }} }}
</style>
</head>
<body>
<header><div class="ancho">
  <div>
    <h1>Optimización de inventario y pronóstico</h1>
    <p class="sub">Supermercados Horizonte Sur · datos sintéticos 2024-2025. Del análisis de
    ventas censuradas al piloto controlado y al caso de negocio, con resultados trazables
    a código y parámetros.</p>
  </div>
  <nav><a href="./">Documentación</a><a href="08-caso-negocio/">Caso de negocio</a>
  <a href="https://github.com/Vaxilium/bi-optimizacion-inventario-retail">GitHub</a></nav>
</div></header>
<main>
  <div class="kpis">{kpis}</div>
  <div class="grid">
    <div class="card ancho">{fragmentos['ventas']}</div>
    <div class="card">{fragmentos['quiebres']}</div>
    <div class="card">{fragmentos['pronostico']}</div>
    <div class="card">{fragmentos['fill']}</div>
    <div class="card">{fragmentos['capital']}</div>
    <div class="card ancho">{fragmentos['piloto']}</div>
    <div class="card ancho">{fragmentos['van']}</div>
    <div class="card ancho">
      <h2 style="font-size:15px;margin:8px 4px 10px;color:#111827;">Beneficios anuales por componente, en la cadena</h2>
      {_tabla_componentes(neg)}
      <p class="pie">Costo de almacenamiento levemente negativo: el capital de trabajo
      adicional es casi nulo. El beneficio se concentra en menos pedidos y menos merma.</p>
    </div>
  </div>
</main>
<footer>Proyecto de portafolio · datos sintéticos con semilla fija · cifras generadas desde
resultados versionados. La verdad oculta de demanda no se usa para entrenar.</footer>
<script>{get_plotlyjs()}</script>
{"".join(fragmentos.values())}
</body>
</html>
"""
    ruta = RAIZ / "docs" / "tablero.html"
    ruta.write_text(html, encoding="utf-8")
    print(f"Tablero generado: {ruta} ({ruta.stat().st_size / 1e6:.1f} MB, {time.time() - inicio:.1f} s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
