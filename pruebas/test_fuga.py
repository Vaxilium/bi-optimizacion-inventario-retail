"""Control estatico: la verdad oculta solo la usan los modulos autorizados."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PERMITIDOS = {
    "src/comun/config.py",
    "src/generacion/generar_datos.py",
    "src/inventario/demanda.py",
    "src/pronostico/censura.py",
}


def test_verdad_oculta_solo_en_modulos_autorizados():
    infractores = []
    for ruta in (RAIZ / "src").rglob("*.py"):
        texto = ruta.read_text(encoding="utf-8")
        relativa = ruta.relative_to(RAIZ).as_posix()
        if ("verdad_demanda" in texto or "RUTA_VERDAD" in texto) and relativa not in PERMITIDOS:
            infractores.append(relativa)
    assert infractores == []
