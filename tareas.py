"""Ejecutor de tareas del proyecto para entornos sin `make`.

Uso:
    python tareas.py todo
    python tareas.py rapido
    python tareas.py sitio
    python tareas.py pruebas
    python tareas.py lint

Los comandos son equivalentes a los del Makefile.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PY = RAIZ / ".venv" / "bin" / "python"
MKDOCS = RAIZ / ".venv" / "bin" / "mkdocs"


def _python() -> str:
    return str(PY) if PY.exists() else sys.executable


def _correr(comando: list[str]) -> None:
    subprocess.run(comando, cwd=RAIZ, check=True)


def _modulo(nombre: str, *argumentos: str) -> None:
    _correr([_python(), "-m", nombre, *argumentos])


def datos(rapido: bool = False) -> None:
    _modulo("src.generacion.generar_datos", *(["--rapido"] if rapido else []))


def capas(rapido: bool = False) -> None:
    _modulo("src.datos.construir_capas", *(["--rapido"] if rapido else []))


def analisis(rapido: bool = False) -> None:
    _modulo("src.analisis_sql.ejecutar", *(["--rapido"] if rapido else []))


def pronostico(rapido: bool = False) -> None:
    _modulo("src.pronostico.ejecutar", *(["--rapido"] if rapido else []))


def inventario(rapido: bool = False) -> None:
    _modulo("src.inventario.ejecutar", *(["--rapido"] if rapido else []))


def piloto(rapido: bool = False) -> None:
    _modulo("src.piloto.ejecutar", *(["--rapido"] if rapido else []))


def negocio(rapido: bool = False) -> None:
    _modulo("src.negocio.caso_negocio", *(["--rapido"] if rapido else []))


def informes(rapido: bool = False) -> None:
    _modulo("src.informes.generar_informes", *(["--rapido"] if rapido else []))


def tablero(rapido: bool = False) -> None:
    _modulo("src.tablero.generar_tablero", *(["--rapido"] if rapido else []))


def pruebas() -> None:
    _correr([_python(), "-m", "pytest", "-q", "pruebas"])


def lint() -> None:
    _correr([_python(), "-m", "ruff", "check", "src", "pruebas"])


def sitio() -> None:
    _correr([str(MKDOCS), "build", "--strict"])


def todo() -> None:
    for tarea in (datos, capas, analisis, pronostico, inventario, piloto, negocio, informes, tablero):
        tarea()
    pruebas()


def rapido() -> None:
    for tarea in (datos, capas, analisis, pronostico, inventario, piloto, negocio, informes, tablero):
        tarea(True)
    pruebas()


TAREAS = {
    "datos": datos, "capas": capas, "analisis": analisis, "pronostico": pronostico,
    "inventario": inventario, "piloto": piloto, "negocio": negocio,
    "informes": informes, "tablero": tablero, "pruebas": pruebas, "lint": lint,
    "sitio": sitio, "todo": todo, "rapido": rapido,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in TAREAS:
        print("Tareas: " + ", ".join(TAREAS))
        raise SystemExit(1)
    TAREAS[sys.argv[1]]()


if __name__ == "__main__":
    main()
