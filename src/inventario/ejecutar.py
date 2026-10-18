"""Simulacion de la politica de reposicion actual vs propuesta.

Uso:
    python -m src.inventario.ejecutar [--rapido]

Salidas:
    resultados/inventario.json
    resultados/tablas/inventario_series.csv
    resultados/tablas/inventario_clase.csv
    resultados/tablas/inventario_ejemplo.csv
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from src.comun.config import RUTA_ALMACEN, asegurar_directorios, cargar_parametros
from src.comun.resultados import guardar_json, guardar_tabla
from src.inventario.contexto import Contexto, construir_contexto
from src.inventario.simulacion import DIAS_CALENTAMIENTO, metricas, simular


def ejecutar(modo_rapido: bool = False) -> dict[str, Any]:
    inicio = time.time()
    parametros = cargar_parametros(modo_rapido)
    asegurar_directorios()
    cfg = parametros["inventario"]
    sim = cfg["simulacion"]
    dias = int(sim["dias"])
    replicas = int(sim["replicas"])
    con = duckdb.connect(str(RUTA_ALMACEN), read_only=True)
    try:
        print("[1/3] Preparando contexto, demanda y stock inicial...")
        contexto = construir_contexto(con, parametros)
        print(
            f"      {len(contexto.pares)} series; factor de censura "
            f"{contexto.factor_censura:.4f}"
        )
        series = []
        ejemplo = None
        for replica in range(replicas):
            semilla = int(sim["semilla_simulacion"]) + replica
            demanda = _demanda_replica(contexto, semilla, dias)
            actual = simular(contexto, demanda, parametros, "actual", semilla + 1)
            propuesta = simular(contexto, demanda, parametros, "propuesta", semilla + 2)
            for politica, resultado in (("actual", actual), ("propuesta", propuesta)):
                tabla = metricas(resultado, contexto, cfg)
                tabla["politica"] = politica
                tabla["replica"] = replica
                series.append(tabla)
            if replica == 0:
                ejemplo = _ejemplo(contexto, demanda, actual, propuesta)
        detalle = pd.concat(series)
        detalle = detalle.merge(
            contexto.pares[["sucursal_id", "producto_id", "clase_abc"]],
            left_index=True, right_index=True,
        )
        print("[2/3] Agregando metricas por politica y clase ABC...")
        resumen = {
            "actual": _agregar(detalle, "actual"),
            "propuesta": _agregar(detalle, "propuesta"),
        }
        por_clase = _por_clase(detalle)
        por_replica = _por_replica(detalle)
        mejora = _mejora(resumen)
        print("[3/3] Guardando resultados...")
        guardar_tabla("inventario_series", detalle)
        guardar_tabla("inventario_clase", por_clase)
        guardar_tabla("inventario_ejemplo", ejemplo)
        salida = {
            "parametros": {
                "dias": dias,
                "replicas": replicas,
                "n_series": int(len(contexto.pares)),
                "semilla": int(sim["semilla_simulacion"]),
                "factor_censura": round(contexto.factor_censura, 4),
                "costo_orden": cfg["costo_orden"],
                "tasa_almacenamiento_anual": cfg["tasa_almacenamiento_anual"],
                "costo_quiebre_factor_margen": cfg["costo_quiebre_factor_margen"],
                "nivel_servicio_objetivo": cfg["nivel_servicio_objetivo"],
                "cobertura_maxima_dias": cfg["cobertura_maxima_dias"],
                "factor_tope_actual": cfg["factor_tope_actual"],
                "dias_calentamiento": DIAS_CALENTAMIENTO,
            },
            "resumen": resumen,
            "mejora": mejora,
            "por_clase": por_clase.to_dict(orient="records"),
            "por_replica": por_replica.to_dict(orient="records"),
            "tiempo_segundos": round(time.time() - inicio, 1),
        }
        guardar_json("inventario", salida)
        _imprimir(salida)
        return salida
    finally:
        con.close()


def _demanda_replica(contexto: Contexto, semilla: int, dias: int) -> np.ndarray:
    generador = np.random.default_rng(semilla)
    horizonte = DIAS_CALENTAMIENTO + dias
    historico = contexto.demanda.shape[1] // 28 * 28
    bloques = contexto.demanda[:, :historico].reshape(len(contexto.pares), -1, 28)
    cantidad = int(np.ceil(horizonte / 28))
    indices = generador.integers(0, bloques.shape[1], size=cantidad)
    camino = np.concatenate([bloques[:, i, :] for i in indices], axis=1)
    return camino[:, :horizonte]


def _agregar(detalle: pd.DataFrame, politica: str) -> dict[str, float]:
    datos = detalle[detalle["politica"] == politica]
    por_replica = datos.groupby("replica").agg(
        venta=("venta", "sum"),
        perdida=("perdida", "sum"),
        dias_demanda=("dias_con_demanda", "sum"),
        dias_quiebre=("dias_quiebre", "sum"),
        capital=("stock_valor_promedio", "sum"),
        merma_unidades=("merma_unidades", "sum"),
        merma_valor=("merma_valor", "sum"),
        valor_venta=("valor_venta", "sum"),
        costo_venta=("costo_venta", "sum"),
        margen_bruto=("margen_bruto", "sum"),
        pedidos=("pedidos", "sum"),
        unidades_pedidas=("unidades_pedidas", "sum"),
        costo_orden=("costo_orden", "sum"),
        costo_almacenamiento=("costo_almacenamiento", "sum"),
        costo_quiebre=("costo_quiebre", "sum"),
        costo_merma=("costo_merma", "sum"),
        costo_total=("costo_total", "sum"),
    )
    media = por_replica.mean()
    vendido = float(media["venta"])
    perdido = float(media["perdida"])
    return {
        "fill_rate": vendido / max(vendido + perdido, 1e-9),
        "quiebre": float(media["dias_quiebre"] / max(media["dias_demanda"], 1)),
        "capital_promedio": float(media["capital"]),
        "dias_inventario": float(media["capital"] / max(media["costo_venta"] / 365, 1e-9)),
        "gmroi": float(media["margen_bruto"] / max(media["capital"], 1e-9)),
        "merma_unidades": float(media["merma_unidades"]),
        "merma_valor": float(media["merma_valor"]),
        "merma_pct_ventas": float(media["merma_valor"] / max(media["valor_venta"], 1e-9)),
        "pedidos": float(media["pedidos"]),
        "unidades_pedidas": float(media["unidades_pedidas"]),
        "costo_orden": float(media["costo_orden"]),
        "costo_almacenamiento": float(media["costo_almacenamiento"]),
        "costo_quiebre": float(media["costo_quiebre"]),
        "costo_merma": float(media["costo_merma"]),
        "costo_total": float(media["costo_total"]),
    }


def _por_clase(detalle: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for clase in ["A", "B", "C"]:
        datos = detalle[detalle["clase_abc"] == clase]
        if datos.empty:
            continue
        actual = _agregar(datos, "actual")
        propuesta = _agregar(datos, "propuesta")
        filas.append(
            {
                "clase_abc": clase,
                "series": int(datos[["sucursal_id", "producto_id"]].drop_duplicates().shape[0]),
                **{f"actual_{k}": v for k, v in actual.items()},
                **{f"propuesta_{k}": v for k, v in propuesta.items()},
                "mejora_fill_pp": (propuesta["fill_rate"] - actual["fill_rate"]) * 100,
                "mejora_capital_pct": (propuesta["capital_promedio"] / max(actual["capital_promedio"], 1e-9) - 1) * 100,
                "mejora_costo_pct": (propuesta["costo_total"] / max(actual["costo_total"], 1e-9) - 1) * 100,
            }
        )
    return pd.DataFrame(filas)


def _por_replica(detalle: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for replica in sorted(detalle["replica"].unique()):
        datos = detalle[detalle["replica"] == replica]
        actual = _agregar(datos, "actual")
        propuesta = _agregar(datos, "propuesta")
        filas.append(
            {
                "replica": int(replica),
                **{f"actual_{k}": v for k, v in actual.items()},
                **{f"propuesta_{k}": v for k, v in propuesta.items()},
                "ahorro": actual["costo_total"] - propuesta["costo_total"],
            }
        )
    return pd.DataFrame(filas)


def _mejora(resumen: dict[str, dict[str, float]]) -> dict[str, float]:
    actual = resumen["actual"]
    propuesta = resumen["propuesta"]
    return {
        "fill_pp": (propuesta["fill_rate"] - actual["fill_rate"]) * 100,
        "quiebre_pp": (propuesta["quiebre"] - actual["quiebre"]) * 100,
        "capital_pct": (propuesta["capital_promedio"] / actual["capital_promedio"] - 1) * 100,
        "capital_liberado": actual["capital_promedio"] - propuesta["capital_promedio"],
        "merma_pct": (propuesta["merma_valor"] / actual["merma_valor"] - 1) * 100,
        "costo_pct": (propuesta["costo_total"] / actual["costo_total"] - 1) * 100,
        "ahorro_anual": actual["costo_total"] - propuesta["costo_total"],
        "pedidos_pct": (propuesta["pedidos"] / actual["pedidos"] - 1) * 100,
        "dias_inventario_pct": (
            propuesta["dias_inventario"] / actual["dias_inventario"] - 1
        ) * 100,
        "gmroi_pct": (propuesta["gmroi"] / actual["gmroi"] - 1) * 100,
    }


def _ejemplo(
    contexto: Contexto,
    demanda: np.ndarray,
    actual: dict[str, np.ndarray],
    propuesta: dict[str, np.ndarray],
) -> pd.DataFrame:
    volumen = demanda[:, DIAS_CALENTAMIENTO:].sum(axis=1)
    clase_a = np.flatnonzero(contexto.clase_abc == "A")
    indices = clase_a[np.argsort(volumen[clase_a])[-3:]]
    fechas = pd.date_range("2026-01-01", periods=demanda.shape[1] - DIAS_CALENTAMIENTO, freq="D")
    bloques = []
    for indice in indices:
        fila = contexto.pares.iloc[indice]
        bloques.append(
            pd.DataFrame(
                {
                    "fecha": fechas,
                    "sucursal_id": fila["sucursal_id"],
                    "producto_id": fila["producto_id"],
                    "clase_abc": fila["clase_abc"],
                    "demanda": demanda[indice, DIAS_CALENTAMIENTO:],
                    "venta_actual": actual["venta"][indice, DIAS_CALENTAMIENTO:],
                    "perdida_actual": actual["perdida"][indice, DIAS_CALENTAMIENTO:],
                    "stock_actual": actual["stock_cierre"][indice, DIAS_CALENTAMIENTO:],
                    "venta_propuesta": propuesta["venta"][indice, DIAS_CALENTAMIENTO:],
                    "perdida_propuesta": propuesta["perdida"][indice, DIAS_CALENTAMIENTO:],
                    "stock_propuesta": propuesta["stock_cierre"][indice, DIAS_CALENTAMIENTO:],
                }
            )
        )
    return pd.concat(bloques, ignore_index=True)


def _imprimir(salida: dict[str, Any]) -> None:
    r = salida["resumen"]
    m = salida["mejora"]
    print(
        f"      fill rate {r['actual']['fill_rate']:.2%} -> {r['propuesta']['fill_rate']:.2%} "
        f"({m['fill_pp']:+.2f} pp); quiebre {r['actual']['quiebre']:.2%} -> "
        f"{r['propuesta']['quiebre']:.2%}; capital {m['capital_pct']:+.1f}%; "
        f"merma {m['merma_pct']:+.1f}%; costo total {m['costo_pct']:+.1f}% "
        f"(ahorro {m['ahorro_anual']:,.0f} UM)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
