"""Pruebas unitarias de la politica de reposicion y sus metricas."""

import numpy as np
import pandas as pd
import pytest

from src.inventario.contexto import Contexto
from src.inventario.simulacion import DIAS_CALENTAMIENTO, _cantidad_propuesta, metricas


def _contexto() -> Contexto:
    n = 3
    return Contexto(
        pares=pd.DataFrame({"sucursal_id": ["S1"] * n, "producto_id": ["P1", "P2", "P3"]}),
        demanda=np.zeros((n, 1)),
        pack=np.array([1.0, 4.0, 2.0]),
        vida=np.array([100.0, 100.0, 100.0]),
        perecedero=np.array([False, False, False]),
        costo=np.array([10.0, 10.0, 10.0]),
        precio=np.array([15.0, 15.0, 15.0]),
        margen=np.array([5.0, 5.0, 5.0]),
        lead_media=np.array([2.0, 2.0, 2.0]),
        lead_sd=np.array([0.0, 0.0, 0.0]),
        frecuencia=np.array([7, 7, 7]),
        fase=np.zeros(n, dtype=int),
        clase_abc=np.array(["A", "B", "C"]),
        servicio=np.array([1.96, 1.64, 1.40]),
        presentacion=np.array([1.0, 4.0, 2.0]),
        factor_censura=1.0,
    )


def _cfg() -> dict:
    return {
        "costo_orden": 42.0,
        "tasa_almacenamiento_anual": 0.19,
        "cobertura_maxima_dias": 14.0,
        "factor_tope_actual": 0.965,
    }


def test_politica_no_pide_si_la_posicion_supera_el_punto_de_pedido():
    contexto = _contexto()
    cantidad = _cantidad_propuesta(
        np.array([10.0, 20.0, 30.0]), np.zeros(3), contexto, np.array([1000.0] * 3), _cfg(), 2.5
    )
    assert np.array_equal(cantidad, np.zeros(3))


def test_politica_redondea_al_pack_y_respeta_el_tope_de_cobertura():
    contexto = _contexto()
    pronostico = np.array([10.0, 20.0, 30.0])
    cantidad = _cantidad_propuesta(
        pronostico, np.zeros(3), contexto, np.zeros(3), _cfg(), 2.5
    )
    assert np.all(cantidad > 0)
    assert np.allclose(cantidad % contexto.pack, 0)
    assert np.all(cantidad <= pronostico * 14.0 * 0.965 + contexto.pack)


def test_metricas_calculan_fill_rate_y_costo_de_quiebre():
    contexto = _contexto()
    dias = DIAS_CALENTAMIENTO + 2
    resultado = {
        "venta": np.ones((3, dias)),
        "perdida": np.zeros((3, dias)),
        "stock_cierre": np.full((3, dias), 2.0),
        "merma": np.zeros((3, dias)),
        "pedidos": np.zeros((3, dias)),
        "quiebre": np.zeros((3, dias), dtype=bool),
    }
    resultado["perdida"][0, -1] = 1.0
    cfg = {"costo_orden": 42.0, "tasa_almacenamiento_anual": 0.19, "costo_quiebre_factor_margen": 1.0}
    marco = metricas(resultado, contexto, cfg)
    assert marco.loc[0, "fill_rate"] == pytest.approx(2 / 3)
    assert marco.loc[0, "costo_quiebre"] == pytest.approx(5.0)
    assert marco.loc[1, "fill_rate"] == pytest.approx(1.0)
    assert marco.loc[1, "costo_almacenamiento"] == pytest.approx(2 * 10 * 2 * 0.19 / 365)
