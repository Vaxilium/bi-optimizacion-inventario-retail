"""Metricas de error para el backtesting de pronosticos."""

from __future__ import annotations

import numpy as np
import pandas as pd


def metricas(y: np.ndarray, yhat: np.ndarray, mae_naive: float) -> dict[str, float]:
    y = np.asarray(y, dtype=float)
    yhat = np.maximum(np.asarray(yhat, dtype=float), 0)
    error = y - yhat
    mae = float(np.mean(np.abs(error)))
    semanas = np.arange(len(y)) // 7
    error_abs_semanal = float(
        sum(abs(error[semanas == semana].sum()) for semana in np.unique(semanas))
    )
    return {
        "mae": mae,
        "rmse": float(np.sqrt(np.mean(error**2))),
        "wape": float(np.abs(error).sum() / max(y.sum(), 1e-9)),
        "sesgo": float(error.sum() / max(y.sum(), 1e-9)),
        "mase": mae / mae_naive if mae_naive > 0 else np.nan,
        "error_abs": float(np.abs(error).sum()),
        "error_firmado": float(error.sum()),
        "error_abs_semanal": error_abs_semanal,
        "error_firmado_semanal": float(error.sum()),
        "unidades_semanal": float(y.sum()),
        "error_cuad": float((error**2).sum()),
        "unidades": float(y.sum()),
        "observaciones": int(len(y)),
    }


def agregar(registros: pd.DataFrame) -> pd.DataFrame:
    """Agrega errores por modelo ponderando por unidades reales."""
    filas = []
    for modelo, grupo in registros.groupby("modelo"):
        total_unidades = grupo["unidades"].sum()
        filas.append(
            {
                "modelo": modelo,
                "wape": grupo["error_abs"].sum() / max(total_unidades, 1e-9),
                "wape_semanal": grupo["error_abs_semanal"].sum()
                / max(grupo["unidades_semanal"].sum(), 1e-9),
                "mae_medio": grupo["mae"].mean(),
                "rmse": np.sqrt(grupo["error_cuad"].sum() / grupo["observaciones"].sum()),
                "mase_medio": grupo["mase"].mean(),
                "wape_mediano": grupo["wape"].median(),
                "series": grupo["identificador"].nunique(),
            }
        )
    tabla = pd.DataFrame(filas)
    sesgo = registros.groupby("modelo").apply(
        lambda g: g["error_firmado"].sum() / max(g["unidades"].sum(), 1e-9),
        include_groups=False,
    )
    tabla["sesgo"] = tabla["modelo"].map(sesgo)
    sesgo_semanal = registros.groupby("modelo").apply(
        lambda g: g["error_firmado_semanal"].sum() / max(g["unidades_semanal"].sum(), 1e-9),
        include_groups=False,
    )
    tabla["sesgo_semanal"] = tabla["modelo"].map(sesgo_semanal)
    return tabla.sort_values("wape_semanal").reset_index(drop=True)


def seleccionar_por_segmento(registros: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for segmento, grupo in registros.groupby("segmento"):
        resumen = (
            grupo.groupby("modelo")
            .agg(error_abs=("error_abs_semanal", "sum"), unidades=("unidades_semanal", "sum"))
            .assign(wape_semanal=lambda d: d["error_abs"] / d["unidades"].clip(lower=1e-9))
            .sort_values("wape_semanal")
        )
        mejor = resumen.index[0]
        base = (
            resumen.loc["media_movil_28", "wape_semanal"]
            if "media_movil_28" in resumen.index else np.nan
        )
        filas.append(
            {
                "segmento": segmento,
                "modelo": mejor,
                "wape_semanal": resumen.loc[mejor, "wape_semanal"],
                "mejora_vs_actual": 1 - resumen.loc[mejor, "wape_semanal"] / base
                if base > 0 else np.nan,
                "series": grupo["identificador"].nunique(),
                "alternativas": ", ".join(resumen.index.tolist()),
            }
        )
    return pd.DataFrame(filas).sort_values("segmento").reset_index(drop=True)
