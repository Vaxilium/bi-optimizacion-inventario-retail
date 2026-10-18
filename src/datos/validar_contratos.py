"""Validador de contratos de datos en YAML.

Falla (exit code distinto de 0) si una tabla del nucleo incumple tipos,
nulabilidad, unicidad, rangos, integridad referencial o volumen minimo.
"""

from __future__ import annotations

import json
from typing import Any

import duckdb
import yaml

from src.comun.config import RUTA_CONTRATOS, RUTA_RESULTADOS

TIPOS_EQUIVALENTES = {
    "INTEGER": {"INTEGER", "BIGINT", "SMALLINT", "TINYINT"},
    "DOUBLE": {"DOUBLE", "REAL", "DECIMAL", "NUMERIC"},
    "VARCHAR": {"VARCHAR", "STRING", "TEXT"},
}


def _compatible(tipo_real: str, tipo_contrato: str) -> bool:
    real = tipo_real.upper()
    esperado = tipo_contrato.upper()
    if esperado in TIPOS_EQUIVALENTES and real in TIPOS_EQUIVALENTES[esperado]:
        return True
    return real == esperado or real.startswith(esperado)


def cargar_contratos() -> dict[str, dict[str, Any]]:
    contratos = {}
    for ruta in sorted(RUTA_CONTRATOS.glob("*.yml")):
        with open(ruta, encoding="utf-8") as archivo:
            contrato = yaml.safe_load(archivo)
        contratos[contrato["tabla"]] = contrato
    return contratos


def validar_contratos(con: duckdb.DuckDBPyConnection, guardar: bool = True) -> list[dict]:
    contratos = cargar_contratos()
    resultados = []
    errores = []
    for tabla, contrato in contratos.items():
        resultados.extend(_validar_tabla(con, tabla, contrato, errores))
    resumen = {
        "tablas": len(contratos),
        "chequeos": len(resultados),
        "fallidos": len(errores),
        "detalle": resultados,
    }
    if guardar:
        RUTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
        with open(RUTA_RESULTADOS / "contratos.json", "w", encoding="utf-8") as archivo:
            json.dump(resumen, archivo, ensure_ascii=False, indent=2, default=str)
    if errores:
        mensaje = "\n".join(f"- {e}" for e in errores)
        raise ValueError(f"Contratos incumplidos ({len(errores)}):\n{mensaje}")
    return resultados


def _registrar(resultados: list, errores: list, tabla: str, chequeo: str, ok: bool, detalle: str) -> None:
    resultados.append({"tabla": tabla, "chequeo": chequeo, "ok": bool(ok), "detalle": detalle})
    if not ok:
        errores.append(f"{tabla} :: {chequeo} :: {detalle}")


def _validar_tabla(
    con: duckdb.DuckDBPyConnection, tabla: str, contrato: dict, errores: list,
) -> list[dict]:
    resultados: list[dict] = []
    try:
        descripcion = con.execute(f"DESCRIBE {tabla}").fetchdf()
    except duckdb.Error as exc:
        _registrar(resultados, errores, tabla, "existencia", False, str(exc))
        return resultados
    tipos = dict(zip(descripcion["column_name"], descripcion["column_type"]))
    _registrar(resultados, errores, tabla, "existencia", True, f"{len(tipos)} columnas")

    for columna in contrato["columnas"]:
        nombre, tipo = columna["nombre"], columna["tipo"]
        if nombre not in tipos:
            _registrar(resultados, errores, tabla, f"columna {nombre}", False, "no existe")
            continue
        _registrar(
            resultados, errores, tabla, f"tipo {nombre}",
            _compatible(tipos[nombre], tipo), f"{tipos[nombre]} vs {tipo}",
        )
        if not columna.get("nulo", True):
            consulta = con.execute(
                f"SELECT COUNT(*) FILTER (WHERE {nombre} IS NULL) FROM {tabla}"
            ).fetchone()[0]
            _registrar(
                resultados, errores, tabla, f"nulabilidad {nombre}",
                consulta == 0, f"{consulta} nulos",
            )

    filas = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    minimo = contrato.get("filas_minimas", 0)
    _registrar(resultados, errores, tabla, "volumen", filas >= minimo, f"{filas} filas (min {minimo})")

    columnas_unicas = contrato.get("unicidad", [])
    if columnas_unicas:
        lista = ", ".join(columnas_unicas)
        duplicados = con.execute(
            f"SELECT COUNT(*) FROM (SELECT {lista} FROM {tabla} GROUP BY {lista} HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        _registrar(
            resultados, errores, tabla, "unicidad", duplicados == 0,
            f"{duplicados} claves duplicadas de ({lista})",
        )

    for columna, limites in contrato.get("rangos", {}).items():
        minimo_real, maximo_real = con.execute(
            f"SELECT MIN({columna}), MAX({columna}) FROM {tabla}"
        ).fetchone()
        for etiqueta, valor_real, limite in (
            ("minimo", minimo_real, limites.get("min")),
            ("maximo", maximo_real, limites.get("max")),
        ):
            if limite is None:
                continue
            ok = _comparar(valor_real, limite, etiqueta)
            _registrar(
                resultados, errores, tabla, f"rango {columna} ({etiqueta})",
                ok, f"{valor_real} vs {limite}",
            )

    for fk in contrato.get("claves_foraneas", []):
        columnas = fk["columnas"]
        condicion = " AND ".join(f"d.{c} = f.{c}" for c in columnas)
        nulos = " AND ".join(f"f.{c} IS NOT NULL" for c in columnas)
        huerfanas = con.execute(
            f"SELECT COUNT(*) FROM {tabla} f LEFT JOIN {fk['tabla']} d ON {condicion} "
            f"WHERE {nulos} AND d.{fk['columna']} IS NULL"
        ).fetchone()[0]
        _registrar(
            resultados, errores, tabla, f"fk {', '.join(columnas)} -> {fk['tabla']}",
            huerfanas == 0, f"{huerfanas} huerfanas",
        )
    return resultados


def _comparar(valor_real: Any, limite: Any, etiqueta: str) -> bool:
    if valor_real is None:
        return False
    try:
        if etiqueta == "minimo":
            return valor_real >= limite
        return valor_real <= limite
    except TypeError:
        return str(valor_real) >= str(limite) if etiqueta == "minimo" else str(valor_real) <= str(limite)
