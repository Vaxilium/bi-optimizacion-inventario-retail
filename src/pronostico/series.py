"""Construccion de series diarias y muestreo estratificado ABC-XYZ."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd


@dataclass
class Serie:
    sucursal_id: str
    producto_id: str
    clase_abc: str
    clase_xyz: str
    fechas: pd.DatetimeIndex
    unidades: np.ndarray
    promociones: np.ndarray
    quiebres: np.ndarray

    @property
    def identificador(self) -> str:
        return f"{self.sucursal_id}-{self.producto_id}"

    @property
    def segmento(self) -> str:
        return f"{self.clase_abc}-{self.clase_xyz}"


def cargar_ventas(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Carga ventas diarias a nivel sucursal-SKU con marca de promocion."""
    return con.execute(
        """
        SELECT
            fecha,
            sucursal_id,
            producto_id,
            SUM(venta_unidades) AS unidades,
            MAX(CASE WHEN en_promocion THEN 1 ELSE 0 END) AS promocion,
            MAX(CASE WHEN indicador_quiebre THEN 1 ELSE 0 END) AS quiebre
        FROM nucleo_hechos_ventas
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
        """
    ).fetchdf()


def clasificar_xyz(valores: np.ndarray) -> str:
    """Clasifica la demanda en X (estable), Y (erratica) o Z (intermitente)."""
    valores = np.asarray(valores, dtype=float)
    no_cero = valores[valores > 0]
    if len(no_cero) < 5:
        return "Z"
    adi = len(valores) / len(no_cero)
    cv2 = (no_cero.std(ddof=1) / no_cero.mean()) ** 2
    if adi > 1.32 or cv2 >= 1.0:
        return "Z"
    return "X" if cv2 < 0.5 else "Y"


def clases_abc(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Clasifica el surtido en A, B o C segun la participacion acumulada de ventas."""
    return con.execute(
        """
        WITH base AS (
            SELECT
                producto_id,
                CAST(ROUND(SUM(ventas), 2) AS DECIMAL(18, 2)) AS ventas
            FROM mart_sku_resumen
            GROUP BY 1
        )
        SELECT producto_id, clase_abc
        FROM (
            SELECT
                producto_id,
                CASE
                    WHEN SUM(ventas) OVER (ORDER BY ventas DESC, producto_id)
                         / SUM(ventas) OVER () <= 0.80 THEN 'A'
                    WHEN SUM(ventas) OVER (ORDER BY ventas DESC, producto_id)
                         / SUM(ventas) OVER () <= 0.95 THEN 'B'
                    ELSE 'C'
                END AS clase_abc
            FROM base
        )
        """
    ).fetchdf()


def estadisticas_pares(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Resumen diario por par para clasificar XYZ y muestrear."""
    df = con.execute(
        """
        SELECT
            sucursal_id,
            producto_id,
            COUNT(*) AS dias,
            COUNT(*) FILTER (WHERE venta_unidades > 0) AS dias_con_venta,
            AVG(venta_unidades) FILTER (WHERE venta_unidades > 0) AS media_no_cero,
            STDDEV_SAMP(venta_unidades) FILTER (WHERE venta_unidades > 0) AS sd_no_cero
        FROM nucleo_hechos_ventas
        GROUP BY 1, 2
        """
    ).fetchdf()
    df = df.merge(clases_abc(con), on="producto_id", how="inner")
    df["adi"] = df["dias"] / df["dias_con_venta"].clip(lower=1)
    df["cv2"] = ((df["sd_no_cero"] / df["media_no_cero"].clip(lower=1e-9)) ** 2).round(8)
    df["clase_xyz"] = np.where(
        (df["adi"] > 1.32) | (df["cv2"] >= 1.0), "Z",
        np.where(df["cv2"] < 0.5, "X", "Y"),
    )
    return df


def _cuotas(tamanos: dict, n: int) -> dict:
    total = sum(tamanos.values())
    n = min(n, total)
    cuotas = {estrato: 0 for estrato in tamanos}
    if n >= len(tamanos):
        for estrato in cuotas:
            cuotas[estrato] = 1
    restante = n - sum(cuotas.values())
    if restante > 0:
        proporcion = {
            estrato: restante * tamano / total for estrato, tamano in tamanos.items()
        }
        for estrato, valor in proporcion.items():
            cuotas[estrato] += int(valor)
        falta = n - sum(cuotas.values())
        orden = sorted(
            tamanos, key=lambda e: proporcion[e] - int(proporcion[e]), reverse=True
        )
        posicion = 0
        while falta > 0:
            estrato = orden[posicion % len(orden)]
            if cuotas[estrato] < tamanos[estrato]:
                cuotas[estrato] += 1
                falta -= 1
            posicion += 1
    return cuotas


def muestrear(pares: pd.DataFrame, n: int, semilla: int) -> pd.DataFrame:
    """Selecciona pares de forma estratificada por ABC-XYZ, con cuotas proporcionales."""
    pares = pares.sort_values(["sucursal_id", "producto_id"]).reset_index(drop=True)
    tamanos = pares.groupby(["clase_abc", "clase_xyz"]).size().to_dict()
    cuotas = _cuotas(tamanos, n)
    generador = np.random.default_rng(semilla)
    elegidos = []
    for abc, xyz in sorted(tamanos):
        grupo = pares[(pares["clase_abc"] == abc) & (pares["clase_xyz"] == xyz)]
        cantidad = min(cuotas[(abc, xyz)], len(grupo))
        if cantidad == 0:
            continue
        indices = generador.choice(len(grupo), size=cantidad, replace=False)
        elegidos.append(grupo.iloc[indices])
    return (
        pd.concat(elegidos, ignore_index=True)
        .sort_values(["sucursal_id", "producto_id"])
        .reset_index(drop=True)
    )


def construir_series(
    ventas: pd.DataFrame, pares: pd.DataFrame, columnas_id: tuple[str, str]
) -> list[Serie]:
    """Reindexa cada par a un calendario diario completo y arma las series."""
    fechas = pd.date_range(ventas["fecha"].min(), ventas["fecha"].max(), freq="D")
    series = []
    for fila in pares.itertuples(index=False):
        sub = ventas[
            (ventas[columnas_id[0]] == getattr(fila, columnas_id[0]))
            & (ventas[columnas_id[1]] == getattr(fila, columnas_id[1]))
        ].set_index("fecha")
        sub = sub.reindex(fechas, fill_value=0)
        series.append(
            Serie(
                sucursal_id=fila.sucursal_id,
                producto_id=fila.producto_id,
                clase_abc=fila.clase_abc,
                clase_xyz=fila.clase_xyz,
                fechas=fechas,
                unidades=sub["unidades"].to_numpy(dtype=float),
                promociones=sub["promocion"].to_numpy(dtype=float),
                quiebres=sub["quiebre"].to_numpy(dtype=float),
            )
        )
    return series
