# Makefile del proyecto. Ejecutar `make todo` para reproducir todo desde cero.
PY := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff

.PHONY: ayuda instalar datos capas analisis pronostico inventario piloto negocio informes tablero sitio pruebas lint todo rapido limpiar

ayuda:
	@echo "Objetivos disponibles:"
	@echo "  make instalar    Instala dependencias en .venv"
	@echo "  make todo        Pipeline completo (reproducible desde cero)"
	@echo "  make rapido      Pipeline reducido (CI / validacion rapida)"
	@echo "  make datos       Genera datos sinteticos (crudo + verdad oculta)"
	@echo "  make capas       Construye capas crudo -> staging -> nucleo -> marts"
	@echo "  make analisis    Analisis exploratorio en SQL"
	@echo "  make pronostico  Backtesting de modelos de pronostico"
	@echo "  make inventario  Simulacion de politica de reposicion"
	@echo "  make piloto      Diseno y analisis del piloto (DiD)"
	@echo "  make negocio     Caso de negocio (Excel con formulas)"
	@echo "  make informes    Genera documentos, README y resumen ejecutivo"
	@echo "  make tablero     Genera docs/tablero.html"
	@echo "  make sitio       Construye el sitio MkDocs"
	@echo "  make pruebas     Ejecuta pytest"
	@echo "  make lint        Ejecuta ruff"
	@echo "  make limpiar     Borra datos y resultados generados"

instalar:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

datos:
	$(PY) -m src.generacion.generar_datos

capas:
	$(PY) -m src.datos.construir_capas

analisis:
	$(PY) -m src.analisis_sql.ejecutar

pronostico:
	$(PY) -m src.pronostico.ejecutar

inventario:
	$(PY) -m src.inventario.ejecutar

piloto:
	$(PY) -m src.piloto.ejecutar

negocio:
	$(PY) -m src.negocio.caso_negocio

informes:
	$(PY) -m src.informes.generar_informes

tablero:
	$(PY) -m src.tablero.generar_tablero

todo: datos capas analisis pronostico inventario piloto negocio informes tablero pruebas

rapido:
	$(PY) -m src.generacion.generar_datos --rapido
	$(PY) -m src.datos.construir_capas --rapido
	$(PY) -m src.analisis_sql.ejecutar --rapido
	$(PY) -m src.pronostico.ejecutar --rapido
	$(PY) -m src.inventario.ejecutar --rapido
	$(PY) -m src.piloto.ejecutar --rapido
	$(PY) -m src.negocio.caso_negocio --rapido
	$(PY) -m src.informes.generar_informes --rapido
	$(PY) -m src.tablero.generar_tablero --rapido
	$(PY) -m pytest -q pruebas

sitio:
	.venv/bin/mkdocs build --strict

pruebas:
	$(PY) -m pytest -q pruebas

lint:
	$(RUFF) check src pruebas tareas.py

limpiar:
	rm -rf datos/crudo datos/staging datos/nucleo datos/marts datos/verdad_oculta datos/almacen
	rm -rf resultados/*.json resultados/tablas site docs/tablero.html
