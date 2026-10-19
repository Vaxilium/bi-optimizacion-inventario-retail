"""Pruebas de la configuracion maestra y del modo rapido."""

import copy

from src.comun.config import cargar_parametros


def test_configuracion_completa():
    parametros = cargar_parametros()
    assert parametros["generacion"]["n_sku"] == 400
    assert parametros["generacion"]["n_sucursales"] == 12
    assert parametros["inventario"]["simulacion"]["n_series"] == 240
    assert parametros["piloto"]["n_tratamiento"] == 4


def test_modo_rapido_recorta_sin_perder_politica():
    parametros = cargar_parametros(True)
    assert parametros["generacion"]["n_sku"] == 40
    assert parametros["generacion"]["n_sucursales"] == 4
    assert parametros["inventario"]["simulacion"]["n_series"] == 24
    assert parametros["inventario"]["simulacion"]["dias"] == 60
    assert parametros["piloto"]["n_tratamiento"] == 1
    assert parametros["inventario"]["factor_tope_actual"] == 0.965
    assert parametros["inventario"]["cobertura_maxima_dias"] == 14.0


def test_modo_rapido_no_muta_la_configuracion_original():
    base = cargar_parametros()
    original = copy.deepcopy(base)
    cargar_parametros(True)
    assert base == original
