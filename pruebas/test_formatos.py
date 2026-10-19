"""Pruebas de los formatos usados en documentos y tablero."""

from src.informes.tablas_md import num, num_opcional, pc, pc_opcional, pp, um


def test_formatos_espanoles():
    assert um(1234) == "1.234"
    assert pc(0.1234) == "12,3%"
    assert pp(1.234) == "+1,23"
    assert num(1234.5, 1) == "1.234,5"
    assert pc_opcional(None) == "n/d"
    assert num_opcional(None) == "n/d"
