"""Caso de negocio: beneficios, inversion, escenarios y archivo Excel con formulas.

Uso:
    python -m src.negocio.caso_negocio [--rapido]

Salidas:
    resultados/negocio.json
    resultados/caso_negocio.xlsx
"""

from __future__ import annotations

import argparse

import duckdb
from scipy.optimize import brentq

from src.comun.config import RUTA_ALMACEN, RUTA_RESULTADOS, cargar_parametros
from src.comun.resultados import guardar_json, leer_json
from src.negocio.excel import generar_excel


def ejecutar(modo_rapido: bool = False) -> dict:
    parametros = cargar_parametros(modo_rapido)
    cfg = parametros["caso_negocio"]
    inventario = leer_json("inventario")
    piloto = leer_json("piloto")
    con = duckdb.connect(str(RUTA_ALMACEN), read_only=True)
    try:
        pares_total = int(
            con.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT sucursal_id, producto_id FROM nucleo_hechos_ventas
                )
                """
            ).fetchone()[0]
        )
    finally:
        con.close()
    pares_muestra = int(inventario["parametros"]["n_series"])
    escala = pares_total / pares_muestra
    efecto_simulado = float(inventario["mejora"]["fill_pp"])
    efecto_piloto = float(piloto["resultado"]["efecto_fill_pp"])
    validacion = min(1.0, efecto_piloto / efecto_simulado) if efecto_simulado else 1.0
    actual = inventario["resumen"]["actual"]
    propuesta = inventario["resumen"]["propuesta"]
    componentes = {
        "costo_orden": actual["costo_orden"] - propuesta["costo_orden"],
        "costo_quiebre": actual["costo_quiebre"] - propuesta["costo_quiebre"],
        "costo_merma": actual["costo_merma"] - propuesta["costo_merma"],
        "costo_almacenamiento": actual["costo_almacenamiento"]
        - propuesta["costo_almacenamiento"],
    }
    ahorro_muestra = float(inventario["mejora"]["ahorro_anual"])
    capital_adicional = float(
        propuesta["capital_promedio"] - actual["capital_promedio"]
    )
    beneficio_anual = ahorro_muestra * escala * validacion
    capital_trabajo = max(0.0, capital_adicional * escala)
    escenarios = {}
    for nombre, multiplicador in cfg["escenarios"].items():
        flujos = _flujos(
            beneficio_anual * float(multiplicador), capital_trabajo, cfg
        )
        escenarios[nombre] = {
            "multiplicador": float(multiplicador),
            "beneficio_anual": beneficio_anual * float(multiplicador),
            "flujos": flujos,
            "van": _van(flujos, float(cfg["tasa_descuento"])),
            "tir": _tir(flujos),
            "payback": _payback(flujos),
        }
    salida = {
        "supuestos": {
            "pares_muestra": pares_muestra,
            "pares_total": pares_total,
            "factor_escala": escala,
            "ahorro_muestra": ahorro_muestra,
            "efecto_simulado_pp": efecto_simulado,
            "efecto_piloto_pp": efecto_piloto,
            "factor_validacion": validacion,
            "beneficio_anual": beneficio_anual,
            "capital_adicional_muestra": capital_adicional,
            "capital_trabajo": capital_trabajo,
            "costo_implementacion": float(cfg["costo_implementacion"]),
            "costo_cambio_procesos": float(cfg["costo_cambio_procesos"]),
            "inversion_inicial": float(
                cfg["costo_implementacion"] + cfg["costo_cambio_procesos"]
            ),
            "costo_operacion_anual": float(cfg["costo_operacion_anual"]),
            "tasa_descuento": float(cfg["tasa_descuento"]),
            "tasa_impuesto": float(cfg["impuesto"]),
            "anios": int(cfg["anios"]),
            "rampa_beneficios": [float(x) for x in cfg["rampa_beneficios"]],
        },
        "componentes_muestra": componentes,
        "componentes": {
            clave: valor * escala * validacion
            for clave, valor in componentes.items()
        },
        "escenarios": escenarios,
    }
    guardar_json("negocio", salida)
    generar_excel(salida, RUTA_RESULTADOS / "caso_negocio.xlsx")
    _imprimir(salida)
    return salida


def _flujos(beneficio: float, capital_trabajo: float, cfg: dict) -> list[float]:
    anios = int(cfg["anios"])
    inversion = float(cfg["costo_implementacion"] + cfg["costo_cambio_procesos"])
    operacion = float(cfg["costo_operacion_anual"])
    impuesto = float(cfg["impuesto"])
    depreciacion = inversion / anios
    flujos = [-(inversion + capital_trabajo)]
    for anio in range(anios):
        ingreso = beneficio * float(cfg["rampa_beneficios"][anio])
        ebit = ingreso - operacion - depreciacion
        impuestos = max(0.0, ebit) * impuesto
        flujo = ingreso - operacion - impuestos
        if anio == anios - 1:
            flujo += capital_trabajo
        flujos.append(flujo)
    return [round(x, 2) for x in flujos]


def _van(flujos: list[float], tasa: float) -> float:
    return sum(f / (1 + tasa) ** t for t, f in enumerate(flujos))


def _tir(flujos: list[float]) -> float | None:
    try:
        return float(brentq(lambda r: _van(flujos, r), -0.99, 10.0))
    except ValueError:
        return None


def _payback(flujos: list[float]) -> float | None:
    acumulado = 0.0
    for anio, flujo in enumerate(flujos):
        anterior = acumulado
        acumulado += flujo
        if acumulado >= 0 and anio > 0:
            if flujo == 0:
                return float(anio)
            return anio - 1 + (-anterior / flujo)
    return None


def _imprimir(datos: dict) -> None:
    base = datos["escenarios"]["base"]
    tir = f"{base['tir']:.1%}" if base["tir"] is not None else "n/d"
    payback = f"{base['payback']:.2f} anios" if base["payback"] is not None else "n/d"
    print(
        f"      beneficio anual {datos['supuestos']['beneficio_anual']:,.0f} UM; "
        f"VAN {base['van']:,.0f} UM; TIR {tir}; payback {payback}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
