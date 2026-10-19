"""Pruebas de las funciones financieras del caso de negocio."""

import pytest

from src.negocio.caso_negocio import _flujos, _payback, _tir, _van


def test_van_suma_flujos_a_tasa_cero():
    assert _van([-100.0, 60.0, 60.0], 0.0) == pytest.approx(20.0)


def test_tir_resuelve_el_punto_de_equilibrio():
    tir = _tir([-100.0, 0.0, 0.0, 133.1])
    assert tir == pytest.approx(0.10, abs=1e-6)


def test_payback_interpola_el_ano_de_recuperacion():
    assert _payback([-100.0, 50.0, 60.0]) == pytest.approx(1 + 50 / 60)


def test_payback_sin_recuperacion():
    assert _payback([-100.0, 10.0]) is None


def test_flujos_incluyen_capital_de_trabajo_en_el_ultimo_ano():
    cfg = {
        "anios": 3,
        "costo_implementacion": 100.0,
        "costo_cambio_procesos": 0.0,
        "costo_operacion_anual": 0.0,
        "impuesto": 0.0,
        "rampa_beneficios": [1.0, 1.0, 1.0],
    }
    flujos = _flujos(100.0, 10.0, cfg)
    assert flujos[0] == pytest.approx(-110.0)
    assert flujos[1] == pytest.approx(100.0)
    assert flujos[2] == pytest.approx(100.0)
    assert flujos[3] == pytest.approx(110.0)
