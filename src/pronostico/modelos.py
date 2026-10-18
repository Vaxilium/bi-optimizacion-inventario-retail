"""Modelos de pronostico con interfaz comun: reciben historia y devuelven 28 dias."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

MODELOS = ["naive_estacional", "media_movil_28", "ets", "croston_sba", "hgbm"]
MODELOS_SIN_CENSURA = ["media_movil_28", "ets", "croston_sba", "hgbm"]
MODELOS_AJUSTADOS = ["media_movil_28", "ets"]


def pronosticar(
    modelo: str,
    historia: np.ndarray,
    promociones: np.ndarray,
    fechas_futuras: pd.DatetimeIndex,
    promociones_futuras: np.ndarray,
    parametros: dict,
) -> np.ndarray:
    if modelo == "naive_estacional":
        return _naive_estacional(historia, fechas_futuras)
    if modelo == "media_movil_28":
        return np.repeat(float(np.mean(historia[-28:])), len(fechas_futuras))
    if modelo == "ets":
        return _ets(historia, len(fechas_futuras))
    if modelo == "croston_sba":
        return _croston_sba(historia, parametros["croston"]["alpha"], len(fechas_futuras))
    if modelo == "hgbm":
        return _hgbm(
            historia, promociones, fechas_futuras, promociones_futuras, parametros["hgbm"]
        )
    raise ValueError(f"Modelo desconocido: {modelo}")


def _naive_estacional(historia: np.ndarray, fechas: pd.DatetimeIndex) -> np.ndarray:
    ultima_semana = historia[-7:]
    return np.array([ultima_semana[fecha.dayofweek] for fecha in fechas], dtype=float)


def _ets(historia: np.ndarray, horizonte: int) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    if np.count_nonzero(historia) < 14:
        return np.repeat(float(np.mean(historia[-28:])), horizonte)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo = ExponentialSmoothing(
                historia,
                trend="add",
                damped_trend=True,
                seasonal="add",
                seasonal_periods=7,
                initialization_method="estimated",
            )
            ajuste = modelo.fit(optimized=True, use_brute=False)
            return np.maximum(np.asarray(ajuste.forecast(horizonte)), 0)
    except Exception:
        return np.repeat(float(np.mean(historia[-28:])), horizonte)


def _croston_sba(historia: np.ndarray, alpha: float, horizonte: int) -> np.ndarray:
    indices = np.flatnonzero(historia > 0)
    if len(indices) == 0:
        return np.zeros(horizonte)
    demanda = historia[indices]
    intervalos = np.diff(np.concatenate(([0], indices))).astype(float)
    z_hat = float(demanda[0])
    q_hat = float(intervalos[0])
    for z, q in zip(demanda[1:], intervalos[1:]):
        z_hat = alpha * z + (1 - alpha) * z_hat
        q_hat = alpha * q + (1 - alpha) * q_hat
    tasa = z_hat / max(q_hat, 1e-9) * (1 - alpha / 2)
    return np.repeat(max(tasa, 0.0), horizonte)


def _fila_hgbm(historia: list[float], fecha: pd.Timestamp, promocion: float) -> list[float]:
    ventana = np.asarray(historia[-28:], dtype=float)
    return [
        historia[-1],
        historia[-7],
        historia[-14],
        historia[-28],
        float(ventana[-7:].mean()),
        float(ventana.mean()),
        float(ventana[-7:].std(ddof=0)),
        float(fecha.dayofweek),
        float(fecha.month),
        float(fecha.dayofweek >= 5),
        promocion,
    ]


def _hgbm(
    historia: np.ndarray,
    promociones: np.ndarray,
    fechas_futuras: pd.DatetimeIndex,
    promociones_futuras: np.ndarray,
    parametros: dict,
) -> np.ndarray:
    from sklearn.ensemble import HistGradientBoostingRegressor

    historia = np.asarray(historia, dtype=float)
    if np.count_nonzero(historia) < 10:
        return np.repeat(float(np.mean(historia[-28:])), len(fechas_futuras))
    fechas_historia = pd.date_range(
        end=fechas_futuras[0] - pd.Timedelta(days=1), periods=len(historia), freq="D"
    )
    serie = pd.Series(historia, index=fechas_historia)
    marco = pd.DataFrame({"y": serie})
    for rezago in (1, 7, 14, 28):
        marco[f"lag_{rezago}"] = marco["y"].shift(rezago)
    marco["mm_7"] = marco["y"].shift(1).rolling(7).mean()
    marco["mm_28"] = marco["y"].shift(1).rolling(28).mean()
    marco["sd_7"] = marco["y"].shift(1).rolling(7).std(ddof=0)
    marco["dow"] = [f.dayofweek for f in fechas_historia]
    marco["mes"] = [f.month for f in fechas_historia]
    marco["finde"] = (marco["dow"] >= 5).astype(float)
    marco["promocion"] = promociones
    columnas = ["lag_1", "lag_7", "lag_14", "lag_28", "mm_7", "mm_28", "sd_7", "dow", "mes", "finde", "promocion"]
    entrenamiento = marco.dropna()
    if len(entrenamiento) < 40:
        return np.repeat(float(np.mean(historia[-28:])), len(fechas_futuras))
    modelo = HistGradientBoostingRegressor(
        max_iter=parametros["max_iter"],
        learning_rate=parametros["learning_rate"],
        max_depth=parametros.get("max_depth"),
        min_samples_leaf=parametros["min_samples_leaf"],
        l2_regularization=1.0,
        early_stopping=False,
        random_state=20240101,
    )
    modelo.fit(entrenamiento[columnas], np.log1p(entrenamiento["y"]))
    historial = historia.tolist()
    pronostico = []
    for fecha, promocion in zip(fechas_futuras, promociones_futuras):
        fila = _fila_hgbm(historial, fecha, float(promocion))
        valor = float(np.expm1(modelo.predict(pd.DataFrame([fila], columns=columnas))[0]))
        valor = max(valor, 0.0)
        pronostico.append(valor)
        historial.append(valor)
    return np.asarray(pronostico)
