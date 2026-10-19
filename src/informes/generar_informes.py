"""Genera documentos Markdown, README y resumen ejecutivo desde los resultados.

Uso:
    python -m src.informes.generar_informes [--rapido]

Salidas:
    README.md
    docs/index.md
    docs/02-datos.md
    docs/04-analisis.md ... docs/08-caso-negocio.md
    docs/10-resumen-ejecutivo.md
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from src.comun.config import RUTA_DOCS, RAIZ, asegurar_directorios, cargar_parametros
from src.comun.resultados import leer_json
from src.informes import secciones

DOCUMENTOS = {
    "02-datos.md": secciones.datos,
    "04-analisis.md": secciones.analisis,
    "05-pronostico.md": secciones.pronostico,
    "06-inventario.md": secciones.inventario,
    "07-piloto.md": secciones.piloto,
    "08-caso-negocio.md": secciones.negocio,
    "10-resumen-ejecutivo.md": secciones.resumen,
}


def ejecutar(modo_rapido: bool = False) -> None:
    inicio = time.time()
    cargar_parametros(modo_rapido)
    asegurar_directorios()
    datos = {
        nombre: leer_json(nombre)
        for nombre in ["generacion", "capa_datos", "analisis", "pronostico", "inventario", "piloto", "negocio"]
    }
    tablas = {
        nombre: pd.read_csv(ruta)
        for nombre, ruta in {
            "analisis_abc_sku": "resultados/tablas/analisis_abc_sku.csv",
            "analisis_quiebres": "resultados/tablas/analisis_quiebres.csv",
            "analisis_inventario": "resultados/tablas/analisis_inventario.csv",
            "analisis_promociones": "resultados/tablas/analisis_promociones.csv",
            "analisis_ventas_mensual": "resultados/tablas/analisis_ventas_mensual.csv",
            "pronostico_seleccion": "resultados/tablas/pronostico_seleccion.csv",
            "inventario_clase": "resultados/tablas/inventario_clase.csv",
            "piloto_sucursales": "resultados/tablas/piloto_sucursales.csv",
        }.items()
    }
    print("[1/2] Generando documentos y README...")
    for nombre, funcion in DOCUMENTOS.items():
        (RUTA_DOCS / nombre).write_text(funcion(datos, tablas), encoding="utf-8")
    (RUTA_DOCS / "index.md").write_text(secciones.inicio(datos, tablas), encoding="utf-8")
    (RAIZ / "README.md").write_text(secciones.readme(datos, tablas), encoding="utf-8")
    print(f"[2/2] {len(DOCUMENTOS)} documentos, index y README actualizados "
          f"({time.time() - inicio:.1f} s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    args = parser.parse_args()
    ejecutar(modo_rapido=args.rapido)
