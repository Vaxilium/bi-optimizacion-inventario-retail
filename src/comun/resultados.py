"""Funciones de apoyo para guardar y leer resultados intermedios.

Los analisis escriben metricas en JSON (resultados/*.json) y tablas en CSV
(resultados/tablas/*.csv). Los documentos se generan despues leyendo estos
archivos: ninguna cifra del README se escribe a mano.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.comun.config import RUTA_RESULTADOS, RUTA_TABLAS


def guardar_json(nombre: str, datos: dict[str, Any] | list[Any]) -> Path:
    """Guarda un diccionario de metricas como JSON legible (no ASCII escapado)."""
    ruta = RUTA_RESULTADOS / f"{nombre}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def leer_json(nombre: str) -> dict[str, Any] | list[Any]:
    """Lee un JSON de resultados. Lanza FileNotFoundError si la fase aun no corrio."""
    ruta = RUTA_RESULTADOS / f"{nombre}.json"
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def existe_resultado(nombre: str) -> bool:
    return (RUTA_RESULTADOS / f"{nombre}.json").exists()


def guardar_tabla(nombre: str, tabla: pd.DataFrame) -> Path:
    """Guarda una tabla de resultados en CSV con formato espanol (coma decimal)."""
    ruta = RUTA_TABLAS / f"{nombre}.csv"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=False)
    return ruta


def leer_tabla(nombre: str) -> pd.DataFrame:
    return pd.read_csv(RUTA_TABLAS / f"{nombre}.csv")


def formato_moneda(valor: float, decimales: int = 0) -> str:
    """Formatea un monto en unidades monetarias (UM) con separador de miles."""
    return f"{valor:,.{decimales}f}".replace(",", ".")


def formato_pct(valor: float, decimales: int = 1) -> str:
    """Formatea una fraccion como porcentaje en formato espanol."""
    return f"{valor * 100:,.{decimales}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def formato_fecha(fecha: pd.Timestamp | str) -> str:
    """Devuelve la fecha en formato dd/mm/aaaa."""
    return pd.Timestamp(fecha).strftime("%d/%m/%Y")
