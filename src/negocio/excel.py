"""Generacion del libro Excel del caso de negocio con formulas auditables."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

AZUL = "1F3864"
CLARO = "D9E2F3"
VERDE = "E2EFDA"


def generar_excel(datos: dict, ruta: Path) -> None:
    libro = Workbook()
    resumen = libro.active
    resumen.title = "Resumen"
    supuestos = libro.create_sheet("Supuestos")
    beneficios = libro.create_sheet("Beneficios")
    hojas = {}
    for nombre in ["Conservador", "Base", "Optimista"]:
        hojas[nombre] = libro.create_sheet(f"Flujos_{nombre}")
    _hoja_supuestos(supuestos, datos)
    _hoja_beneficios(beneficios, datos)
    for nombre, hoja in hojas.items():
        _hoja_flujos(hoja, nombre, datos)
    _hoja_resumen(resumen, datos, hojas)
    _estilo(libro)
    libro.calculation.fullCalcOnLoad = True
    libro.save(ruta)


def _hoja_supuestos(hoja, datos: dict) -> None:
    s = datos["supuestos"]
    hoja["A1"] = "Caso de negocio: supuestos"
    filas = [
        ("Pares en la simulacion", s["pares_muestra"], "0"),
        ("Pares en la cadena", s["pares_total"], "0"),
        ("Factor de escala", "=B4/B3", "0.00"),
        ("Ahorro anual simulado (240 pares)", s["ahorro_muestra"], "#,##0"),
        ("Efecto fill simulado (pp)", s["efecto_simulado_pp"], "0.00"),
        ("Efecto fill piloto (pp)", s["efecto_piloto_pp"], "0.00"),
        ("Factor de validacion del piloto", "=MIN(1,B8/B7)", "0.00"),
        ("Ahorro anual base en la cadena", "=B5*B6*B9", "#,##0"),
        ("Capital de trabajo adicional (muestra)", s["capital_adicional_muestra"], "#,##0"),
        ("Capital de trabajo adicional (cadena)", "=B11*B5", "#,##0"),
        ("Inversion inicial", "=B14+B15", "#,##0"),
        ("Implementacion", s["costo_implementacion"], "#,##0"),
        ("Cambio de procesos", s["costo_cambio_procesos"], "#,##0"),
        ("Costo de operacion anual", s["costo_operacion_anual"], "#,##0"),
        ("Tasa de impuesto", s["tasa_impuesto"], "0%"),
        ("Tasa de descuento", s["tasa_descuento"], "0%"),
        ("Anios", s["anios"], "0"),
        ("Depreciacion anual", "=B13/B19", "#,##0"),
        ("Ramp-up anio 1", s["rampa_beneficios"][0], "0%"),
        ("Ramp-up anio 2", s["rampa_beneficios"][1], "0%"),
        ("Ramp-up anio 3", s["rampa_beneficios"][2], "0%"),
    ]
    for indice, (etiqueta, valor, formato) in enumerate(filas, start=3):
        hoja.cell(indice, 1, etiqueta)
        celda = hoja.cell(indice, 2, valor)
        celda.number_format = formato
    hoja["A25"] = "Escenarios"
    hoja["A26"], hoja["B26"] = "Conservador", datos["escenarios"]["conservador"]["multiplicador"]
    hoja["A27"], hoja["B27"] = "Base", datos["escenarios"]["base"]["multiplicador"]
    hoja["A28"], hoja["B28"] = "Optimista", datos["escenarios"]["optimista"]["multiplicador"]
    hoja["A30"] = "Beneficios por componente (UM anuales en la cadena)"
    componentes = [
        ("Costo de orden", datos["componentes"]["costo_orden"]),
        ("Costo de quiebre", datos["componentes"]["costo_quiebre"]),
        ("Costo de merma", datos["componentes"]["costo_merma"]),
        ("Costo de almacenamiento", datos["componentes"]["costo_almacenamiento"]),
    ]
    for indice, (etiqueta, valor) in enumerate(componentes, start=31):
        hoja.cell(indice, 1, etiqueta)
        celda = hoja.cell(indice, 2, round(valor, 2))
        celda.number_format = "#,##0"
    hoja["A35"], hoja["B35"] = "Total", "=SUM(B31:B34)"
    hoja["B35"].number_format = "#,##0"


def _hoja_beneficios(hoja, datos: dict) -> None:
    hoja["A1"] = "Beneficios anuales por componente"
    hoja["A3"] = "Componente"
    hoja["B3"] = "Muestra"
    hoja["C3"] = "Factor escala"
    hoja["D3"] = "Validacion piloto"
    hoja["E3"] = "Cadena"
    filas = [
        ("Costo de orden", datos["componentes_muestra"]["costo_orden"]),
        ("Costo de quiebre", datos["componentes_muestra"]["costo_quiebre"]),
        ("Costo de merma", datos["componentes_muestra"]["costo_merma"]),
        ("Costo de almacenamiento", datos["componentes_muestra"]["costo_almacenamiento"]),
    ]
    for indice, (etiqueta, valor) in enumerate(filas, start=4):
        hoja.cell(indice, 1, etiqueta)
        hoja.cell(indice, 2, round(valor, 2))
        hoja.cell(indice, 3, "=Supuestos!$B$5")
        hoja.cell(indice, 4, "=Supuestos!$B$9")
        hoja.cell(indice, 5, f"=B{indice}*C{indice}*D{indice}")
    hoja["A8"], hoja["E8"] = "Total", "=SUM(E4:E7)"


def _hoja_flujos(hoja, nombre: str, datos: dict) -> None:
    multiplicador = {"Conservador": "$B$26", "Base": "$B$27", "Optimista": "$B$28"}[nombre]
    hoja["A1"] = f"Flujos de caja - escenario {nombre.lower()}"
    hoja["A2"] = "Multiplicador de beneficios"
    hoja["B2"] = f"=Supuestos!{multiplicador}"
    hoja["B2"].number_format = "0.00"
    for columna, anio in enumerate(range(4), start=2):
        celda = hoja.cell(3, columna, f"Anio {anio}")
        celda.font = Font(bold=True)
    filas = ["Beneficio", "Costo de operacion", "Depreciacion", "EBIT", "Impuesto",
             "Flujo operativo", "Inversion inicial", "Capital de trabajo", "Flujo neto"]
    for indice, etiqueta in enumerate(filas, start=4):
        hoja.cell(indice, 1, etiqueta)
    for columna, anio in enumerate(range(4), start=2):
        letra = get_column_letter(columna)
        hoja.cell(4, columna, 0 if anio == 0 else f"=Supuestos!$B$10*$B$2*Supuestos!$B${20 + anio}")
        hoja.cell(5, columna, 0 if anio == 0 else "=-Supuestos!$B$16")
        hoja.cell(6, columna, 0 if anio == 0 else "=-Supuestos!$B$20")
        hoja.cell(7, columna, f"=SUM({letra}4:{letra}6)")
        hoja.cell(8, columna, f"=-MAX(0,{letra}7)*Supuestos!$B$17")
        hoja.cell(9, columna, f"={letra}7+{letra}8-{letra}6")
        hoja.cell(10, columna, "=-Supuestos!$B$13" if anio == 0 else 0)
        if anio == 0:
            hoja.cell(11, columna, "=-Supuestos!$B$12")
        elif anio == 3:
            hoja.cell(11, columna, "=Supuestos!$B$12")
        else:
            hoja.cell(11, columna, 0)
        hoja.cell(12, columna, f"=SUM({letra}9:{letra}11)")
    hoja["A14"], hoja["B14"] = "VAN", "=NPV(Supuestos!$B$18,C12:E12)+B12"
    hoja["B14"].number_format = "#,##0"
    hoja["A15"], hoja["B15"] = "TIR", "=IRR(B12:E12)"
    hoja["B15"].number_format = "0.0%"
    hoja["A16"], hoja["B16"] = "Payback (anios)", (
        '=IF(B12>=0,0,IF(C12>=0,1-B12/C12,IF(D12>=0,2-(B12+C12)/D12,'
        'IF(E12>=0,3-(B12+C12+D12)/E12,">3"))))'
    )
    hoja["B16"].number_format = "0.00"
    for fila in range(4, 13):
        for columna in range(2, 6):
            hoja.cell(fila, columna).number_format = "#,##0"


def _hoja_resumen(hoja, datos: dict, hojas: dict) -> None:
    hoja["A1"] = "Caso de negocio: resumen ejecutivo"
    hoja["A3"] = "Indicador"
    hoja["B3"], hoja["C3"], hoja["D3"] = "Conservador", "Base", "Optimista"
    hoja["A4"] = "Multiplicador de beneficios"
    hoja["A5"] = "Beneficio anual (anio 2)"
    hoja["A6"] = "VAN"
    hoja["A7"] = "TIR"
    hoja["A8"] = "Payback (anios)"
    for columna, nombre in enumerate(["conservador", "base", "optimista"], start=2):
        letra = get_column_letter(columna)
        hoja[f"{letra}4"] = f"=Supuestos!$B${25 + columna - 1}"
        hoja[f"{letra}5"] = f"=Supuestos!$B$10*{letra}4"
        hoja[f"{letra}6"] = f"=Flujos_{nombre.capitalize()}!B14"
        hoja[f"{letra}7"] = f"=Flujos_{nombre.capitalize()}!B15"
        hoja[f"{letra}8"] = f"=Flujos_{nombre.capitalize()}!B16"
        hoja[f"{letra}5"].number_format = "#,##0"
        hoja[f"{letra}6"].number_format = "#,##0"
        hoja[f"{letra}7"].number_format = "0.0%"
        hoja[f"{letra}8"].number_format = "0.00"
    hoja["A10"] = "Beneficio anual base en la cadena"
    hoja["B10"] = "=Supuestos!$B$10"
    hoja["B10"].number_format = "#,##0"
    hoja["A11"] = "Inversion inicial + capital de trabajo"
    hoja["B11"] = "=Supuestos!$B$13+Supuestos!$B$12"
    hoja["B11"].number_format = "#,##0"
    hoja["A12"] = "Factor de validacion del piloto"
    hoja["B12"] = "=Supuestos!$B$9"
    hoja["B12"].number_format = "0.00"
    grafico = BarChart()
    grafico.title = "VAN por escenario"
    grafico.y_axis.title = "UM"
    datos_grafico = Reference(hoja, min_col=2, max_col=4, min_row=6, max_row=6)
    categorias = Reference(hoja, min_col=2, max_col=4, min_row=3, max_row=3)
    grafico.add_data(datos_grafico, from_rows=True, titles_from_data=False)
    grafico.set_categories(categorias)
    grafico.height = 7
    grafico.width = 15
    hoja.add_chart(grafico, "A14")


def _estilo(libro: Workbook) -> None:
    for hoja in libro.worksheets:
        hoja.sheet_view.showGridLines = False
        hoja.column_dimensions["A"].width = 42
        for columna in "BCDE":
            hoja.column_dimensions[columna].width = 16
        for celda in hoja[1]:
            celda.font = Font(bold=True, size=14, color="FFFFFF")
        hoja["A1"].fill = PatternFill("solid", fgColor=AZUL)
        for fila in hoja.iter_rows(min_row=3, max_row=3):
            for celda in fila:
                if celda.value is not None:
                    celda.font = Font(bold=True)
                    celda.fill = PatternFill("solid", fgColor=CLARO)
        for fila in hoja.iter_rows(min_row=1, max_row=hoja.max_row):
            for celda in fila:
                if isinstance(celda.value, str) and celda.row > 1:
                    celda.alignment = Alignment(vertical="center")
    libro["Resumen"]["A1"].fill = PatternFill("solid", fgColor=AZUL)
    libro["Resumen"]["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    libro["Resumen"]["B6"].fill = PatternFill("solid", fgColor=VERDE)


