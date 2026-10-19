"""Utilidades de formato y tablas Markdown para los informes generados."""

from __future__ import annotations

from typing import Iterable


def um(valor: float, decimales: int = 0) -> str:
    return f"{valor:,.{decimales}f}".replace(",", ".")


def pc(valor: float, decimales: int = 1) -> str:
    return f"{valor * 100:,.{decimales}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def pp(valor: float, decimales: int = 2) -> str:
    return f"{valor:+,.{decimales}f}".replace(".", ",")


def num(valor: float, decimales: int = 2) -> str:
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pc_opcional(valor: float | None, decimales: int = 1) -> str:
    return "n/d" if valor is None else pc(valor, decimales)


def num_opcional(valor: float | None, decimales: int = 2) -> str:
    return "n/d" if valor is None else num(valor, decimales)


def tabla(encabezados: Iterable[str], filas: Iterable[Iterable[object]], alineacion: str | None = None) -> str:
    encabezados = list(encabezados)
    filas = [list(fila) for fila in filas]
    if alineacion is None:
        alineacion = "---"
    lineas = [
        "| " + " | ".join(str(x) for x in encabezados) + " |",
        "| " + " | ".join(alineacion for _ in encabezados) + " |",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(x) for x in fila) + " |")
    return "\n".join(lineas)
