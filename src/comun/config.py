"""Utilidades comunes: carga de parametros y rutas del proyecto.

Todos los modulos del pipeline importan la configuracion desde aqui para
garantizar que exista una unica fuente de verdad (config/parametros.yaml).
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parents[2]

RUTA_CONFIG = RAIZ / "config" / "parametros.yaml"
RUTA_DATOS = RAIZ / "datos"
RUTA_CRUDO = RUTA_DATOS / "crudo"
RUTA_STAGING = RUTA_DATOS / "staging"
RUTA_NUCLEO = RUTA_DATOS / "nucleo"
RUTA_MARTS = RUTA_DATOS / "marts"
RUTA_VERDAD = RUTA_DATOS / "verdad_oculta"
RUTA_ALMACEN = RUTA_DATOS / "almacen" / "horizonte.duckdb"
RUTA_MUESTRAS = RUTA_DATOS / "muestras"
RUTA_SQL = RAIZ / "sql"
RUTA_RESULTADOS = RAIZ / "resultados"
RUTA_TABLAS = RUTA_RESULTADOS / "tablas"
RUTA_DOCS = RAIZ / "docs"
RUTA_CONTRATOS = RAIZ / "contratos"


def cargar_parametros(modo_rapido: bool = False) -> dict[str, Any]:
    """Carga los parametros y aplica, si corresponde, los recortes del modo rapido."""
    with open(RUTA_CONFIG, encoding="utf-8") as archivo:
        parametros = yaml.safe_load(archivo)
    if modo_rapido:
        parametros = copy.deepcopy(parametros)
        _fusionar(parametros, parametros.get("rapido", {}))
    return parametros


def _fusionar(base: dict[str, Any], encima: dict[str, Any]) -> None:
    for clave, valor in encima.items():
        if isinstance(valor, dict) and isinstance(base.get(clave), dict):
            _fusionar(base[clave], valor)
        else:
            base[clave] = copy.deepcopy(valor)


def asegurar_directorios() -> None:
    """Crea los directorios de datos y resultados si no existen."""
    for ruta in (
        RUTA_CRUDO, RUTA_STAGING, RUTA_NUCLEO, RUTA_MARTS, RUTA_VERDAD,
        RUTA_ALMACEN.parent, RUTA_MUESTRAS, RUTA_RESULTADOS, RUTA_TABLAS,
    ):
        ruta.mkdir(parents=True, exist_ok=True)
