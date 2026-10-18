"""Backtesting rolling-origin contra demanda potencial (evaluacion de censura)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.pronostico.censura import corregir_historia
from src.pronostico.evaluacion import metricas
from src.pronostico.modelos import (
    MODELOS, MODELOS_AJUSTADOS, MODELOS_SIN_CENSURA, pronosticar,
)
from src.pronostico.series import Serie


def ejecutar_backtest(
    series: list[Serie],
    verdad: dict[str, np.ndarray],
    parametros: dict,
    factor_censura: float = 1.0,
) -> tuple[pd.DataFrame, dict[tuple[str, str], np.ndarray], pd.DatetimeIndex]:
    """Genera metricas por serie, origen y modelo contra la demanda potencial."""
    config = parametros["pronostico"]
    horizonte = config["horizonte_dias"]
    origenes = config["origenes"]
    ventana = config["ventana_entrenamiento_dias"]
    cuantil = config["cuantil_censura"]
    ultima = series[0].fechas.max()
    registros = []
    predicciones = {}
    fechas_ultimo = None
    for origen in range(origenes):
        fin_prueba = ultima - pd.Timedelta(days=horizonte * origen)
        inicio_prueba = fin_prueba - pd.Timedelta(days=horizonte - 1)
        fechas_prueba = pd.date_range(inicio_prueba, fin_prueba, freq="D")
        if origen == 0:
            fechas_ultimo = fechas_prueba
        for serie in series:
            posiciones = serie.fechas.get_indexer(fechas_prueba)
            y = verdad[serie.identificador][posiciones]
            promo_futura = serie.promociones[posiciones]
            fin_train = posiciones[0] - 1
            inicio_train = max(0, fin_train - ventana + 1)
            historia = serie.unidades[inicio_train : fin_train + 1]
            quiebres = serie.quiebres[inicio_train : fin_train + 1]
            promo_historia = serie.promociones[inicio_train : fin_train + 1]
            if len(historia) < 28:
                continue
            corregida = corregir_historia(historia, quiebres, cuantil=cuantil)
            naive = pronosticar(
                "naive_estacional", historia, promo_historia, fechas_prueba,
                promo_futura, config,
            )
            mae_naive = float(np.mean(np.abs(y - naive)))
            for modelo in MODELOS:
                yhat = pronosticar(
                    modelo, historia, promo_historia, fechas_prueba,
                    promo_futura, config,
                )
                _registrar(
                    registros, predicciones, serie, modelo, y, yhat,
                    mae_naive, inicio_prueba, origen,
                )
            for modelo in MODELOS_SIN_CENSURA:
                yhat = pronosticar(
                    modelo, corregida, promo_historia, fechas_prueba,
                    promo_futura, config,
                )
                _registrar(
                    registros, predicciones, serie, f"{modelo}_sin_censura", y, yhat,
                    mae_naive, inicio_prueba, origen,
                )
            for modelo in MODELOS_AJUSTADOS:
                yhat = pronosticar(
                    modelo, historia, promo_historia, fechas_prueba,
                    promo_futura, config,
                ) * factor_censura
                _registrar(
                    registros, predicciones, serie, f"{modelo}_ajustada", y, yhat,
                    mae_naive, inicio_prueba, origen,
                )
    return pd.DataFrame(registros), predicciones, fechas_ultimo


def _registrar(
    registros, predicciones, serie, modelo, y, yhat, mae_naive, inicio, origen
) -> None:
    resultado = metricas(y, yhat, mae_naive)
    registros.append(
        {
            "identificador": serie.identificador,
            "sucursal_id": serie.sucursal_id,
            "producto_id": serie.producto_id,
            "clase_abc": serie.clase_abc,
            "clase_xyz": serie.clase_xyz,
            "segmento": serie.segmento,
            "modelo": modelo,
            "origen": inicio.strftime("%Y-%m-%d"),
            **resultado,
        }
    )
    if origen == 0:
        predicciones[(serie.identificador, modelo)] = yhat
