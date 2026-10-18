"""Estimacion de diferencias en diferencias, tendencias paralelas y potencia."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm

CONTROLES = "fill_base + np.log(unidades_base)"


def estimar(panel: pd.DataFrame, asignacion: pd.DataFrame, parametros: dict) -> dict:
    cfg = parametros["piloto"]
    datos = panel.merge(
        asignacion[["sucursal_id", "unidades_base", "tasa_quiebre_base"]].assign(
            fill_base=lambda x: 1 - x["tasa_quiebre_base"]
        ),
        on="sucursal_id",
        how="left",
    )
    modelo_fill = smf.ols(
        f"fill_rate ~ tratamiento + post + tratamiento:post + {CONTROLES}", data=datos
    ).fit(cov_type="HC1")
    modelo_unidades = smf.ols(
        f"unidades ~ tratamiento + post + tratamiento:post + {CONTROLES}", data=datos
    ).fit(cov_type="HC1")
    efecto_fill = float(modelo_fill.params["tratamiento:post"])
    efecto_unidades = float(modelo_unidades.params["tratamiento:post"])
    control_post = float(
        datos[(datos["tratamiento"] == 0) & (datos["post"] == 1)]["unidades"].mean()
    )
    pre = datos[datos["post"] == 0].copy()
    pre["post_falso"] = (pre["semana"] > cfg["semanas_pre"] / 2).astype(int)
    modelo_pre = smf.ols(
        f"fill_rate ~ tratamiento + post_falso + tratamiento:post_falso + {CONTROLES}",
        data=pre,
    ).fit(cov_type="HC1")
    potencia = _potencia(panel, asignacion, efecto_fill, cfg)
    return {
        "efecto_fill_pp": efecto_fill * 100,
        "efecto_fill_ic95": [
            float(modelo_fill.conf_int().loc["tratamiento:post", 0]) * 100,
            float(modelo_fill.conf_int().loc["tratamiento:post", 1]) * 100,
        ],
        "efecto_fill_p": float(modelo_fill.pvalues["tratamiento:post"]),
        "efecto_unidades_semana": efecto_unidades,
        "efecto_unidades_pct": efecto_unidades / max(control_post, 1e-9),
        "efecto_unidades_p": float(modelo_unidades.pvalues["tratamiento:post"]),
        "tendencia_pre_coef_pp": float(modelo_pre.params["tratamiento:post_falso"]) * 100,
        "tendencia_pre_p": float(modelo_pre.pvalues["tratamiento:post_falso"]),
        "tendencias_paralelas": bool(
            modelo_pre.pvalues["tratamiento:post_falso"] > cfg["alfa"]
        ),
        "potencia": potencia,
        "r2_fill": float(modelo_fill.rsquared),
        "observaciones": int(len(datos)),
    }


def _potencia(
    panel: pd.DataFrame,
    asignacion: pd.DataFrame,
    efecto: float,
    cfg: dict,
) -> dict:
    contrafactual = panel.copy()
    contrafactual["fill_actual"] = contrafactual["fill_rate_actual"]
    pre = contrafactual[contrafactual["post"] == 0].groupby("sucursal_id")["fill_actual"].mean()
    post = contrafactual[contrafactual["post"] == 1].groupby("sucursal_id")["fill_actual"].mean()
    cambios = (post - pre).dropna()
    n_t = int(asignacion["tratamiento"].sum())
    n_c = int(len(asignacion) - n_t)
    desvio = float(cambios.std(ddof=1))
    error = desvio * np.sqrt(1 / n_t + 1 / n_c)
    z_alfa = float(norm.ppf(1 - cfg["alfa"] / 2))
    z_potencia = float(norm.ppf(cfg["potencia_objetivo"]))
    mde = (z_alfa + z_potencia) * error
    potencia = float(norm.cdf(abs(efecto) / error - z_alfa)) if error > 0 else 1.0
    return {
        "n_tratamiento": n_t,
        "n_control": n_c,
        "desvio_cambios_pp": desvio * 100,
        "mde_pp": mde * 100,
        "potencia_observada": min(max(potencia, 0.0), 1.0),
        "alfa": float(cfg["alfa"]),
        "potencia_objetivo": float(cfg["potencia_objetivo"]),
    }
