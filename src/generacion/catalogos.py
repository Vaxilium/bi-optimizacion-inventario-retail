"""Catalogos de apoyo para el generador de datos sinteticos.

Contiene nombres de categorias, subcategorias, marcas, ciudades y feriados.
Todo es ficticio; cualquier parecido con empresas reales es coincidencia.
"""

from __future__ import annotations

import datetime as dt

MARCAS = [
    "Valle Sur", "Cumbre Andina", "Doña Rosa", "El Roble", "Mar Azul",
    "Sol Naciente", "La Pradera", "Horizonte", "Río Claro", "Monte Verde",
]

CATEGORIAS: dict[str, dict] = {
    "Abarrotes": {
        "subcategorias": ["Arroz y pastas", "Aceites y vinagres", "Conservas", "Harinas y azúcar"],
        "nombres": ["Arroz largo fino", "Fideos spaghetti", "Aceite vegetal", "Atún en agua",
                    "Harina sin polvo", "Azúcar rubia", "Arroz integral", "Fideos corbata",
                    "Aceite de oliva", "Salsa de tomate"],
        "tamanos": ["500 g", "1 kg", "2 kg", "900 ml", "400 g"],
        "perecible": 0.0, "vida_util": (365, 540), "costo": (0.7, 5.5),
        "margen": (0.18, 0.30), "pack": (12, 24), "dec_navidad": 1.10,
    },
    "Bebidas": {
        "subcategorias": ["Aguas y jugos", "Gaseosas", "Cervezas y vinos", "Energizantes"],
        "nombres": ["Agua mineral", "Jugo de naranja", "Gaseosa cola", "Cerveza lager",
                    "Vino tinto reserva", "Bebida isotónica", "Agua saborizada", "Jugo de durazno",
                    "Gaseosa limón", "Vino blanco"],
        "tamanos": ["500 ml", "1 L", "1,5 L", "2 L", "750 ml"],
        "perecible": 0.0, "vida_util": (270, 540), "costo": (0.4, 8.0),
        "margen": (0.20, 0.35), "pack": (6, 24), "dec_navidad": 1.55,
    },
    "Lacteos": {
        "subcategorias": ["Leches", "Yogures", "Quesos", "Mantequillas"],
        "nombres": ["Leche entera", "Leche descremada", "Yogur natural", "Yogur de frutilla",
                    "Queso gauda", "Queso fresco", "Mantequilla", "Leche condensada",
                    "Crema espesa", "Queso parmesano"],
        "tamanos": ["200 g", "500 g", "1 L", "1 kg", "250 ml"],
        "perecible": 0.9, "vida_util": (7, 45), "costo": (0.5, 6.5),
        "margen": (0.22, 0.36), "pack": (6, 12), "dec_navidad": 1.20,
    },
    "Panaderia": {
        "subcategorias": ["Pan fresco", "Pan envasado", "Tortillas", "Masas dulces"],
        "nombres": ["Pan marraqueta", "Pan de molde", "Pan integral", "Tortilla de trigo",
                    "Pan de hamburguesa", "Pan dulce", "Galleta de agua", "Pan pita",
                    "Bollo de mantequilla", "Pan multigrano"],
        "tamanos": ["300 g", "500 g", "700 g", "1 kg", "8 unid"],
        "perecible": 1.0, "vida_util": (2, 12), "costo": (0.3, 3.0),
        "margen": (0.25, 0.42), "pack": (4, 12), "dec_navidad": 1.25,
    },
    "Carnes": {
        "subcategorias": ["Vacuno", "Pollo", "Cerdo", "Embutidos"],
        "nombres": ["Carne molida", "Lomo de vacuno", "Pechuga de pollo", "Pata de pollo",
                    "Chuleta de cerdo", "Salchichas", "Jamón laminado", "Costilla de cerdo",
                    "Filete de vacuno", "Panceta"],
        "tamanos": ["500 g", "1 kg", "700 g", "250 g", "2 kg"],
        "perecible": 1.0, "vida_util": (3, 10), "costo": (2.5, 14.0),
        "margen": (0.24, 0.38), "pack": (4, 8), "dec_navidad": 1.50,
    },
    "Frutas y verduras": {
        "subcategorias": ["Frutas frescas", "Verduras", "Tubérculos", "Hierbas"],
        "nombres": ["Manzana fuji", "Plátano", "Naranja", "Palta hass", "Tomate",
                    "Lechuga", "Papa, saco", "Zanahoria", "Cebolla", "Limón"],
        "tamanos": ["500 g", "1 kg", "2 kg", "1 unid", "5 kg"],
        "perecible": 1.0, "vida_util": (3, 15), "costo": (0.3, 4.5),
        "margen": (0.25, 0.42), "pack": (4, 10), "dec_navidad": 1.30,
    },
    "Congelados": {
        "subcategorias": ["Comidas preparadas", "Verduras congeladas", "Helados", "Pescados"],
        "nombres": ["Pizza congelada", "Lasagna congelada", "Arvejas congeladas",
                    "Helado de vainilla", "Helado de chocolate", "Filete de merluza",
                    "Nuggets de pollo", "Papas congeladas", "Empanadas congeladas", "Pulpo congelado"],
        "tamanos": ["400 g", "500 g", "1 kg", "1 L", "800 g"],
        "perecible": 0.5, "vida_util": (120, 240), "costo": (1.2, 9.0),
        "margen": (0.26, 0.40), "pack": (6, 12), "dec_navidad": 1.35,
    },
    "Limpieza": {
        "subcategorias": ["Detergentes", "Desinfectantes", "Papel", "Utensilios"],
        "nombres": ["Detergente en polvo", "Detergente líquido", "Cloro", "Limpiador de pisos",
                    "Papel higiénico", "Toalla de papel", "esponja multiuso", "Bolsas de basura",
                    "Lavaloza", "Suavizante"],
        "tamanos": ["500 ml", "1 L", "3 L", "4 unid", "12 unid"],
        "perecible": 0.0, "vida_util": (540, 900), "costo": (0.6, 6.0),
        "margen": (0.20, 0.32), "pack": (6, 18), "dec_navidad": 1.15,
    },
    "Higiene personal": {
        "subcategorias": ["Cuidado del cabello", "Cuidado bucal", "Cuidado de la piel", "Afeitado"],
        "nombres": ["Shampoo", "Acondicionador", "Pasta dental", "Cepillo de dientes",
                    "Jabón de tocador", "Crema corporal", "Desodorante", "Máquina de afeitar",
                    "Gel de ducha", "Protector solar"],
        "tamanos": ["100 ml", "250 ml", "500 ml", "90 g", "2 unid"],
        "perecible": 0.0, "vida_util": (540, 900), "costo": (0.8, 7.5),
        "margen": (0.24, 0.40), "pack": (6, 12), "dec_navidad": 1.20,
    },
    "Snacks": {
        "subcategorias": ["Galletas", "Papas fritas", "Chocolates", "Frutos secos"],
        "nombres": ["Galleta de chocolate", "Galleta de vainilla", "Papas fritas",
                    "Chocolate con leche", "Chocolate amargo", "Maní salado", "Almendras",
                    "Cabritas", "Barra de cereal", "Mix de frutos secos"],
        "tamanos": ["150 g", "200 g", "250 g", "500 g", "40 g"],
        "perecible": 0.1, "vida_util": (120, 270), "costo": (0.5, 4.0),
        "margen": (0.26, 0.42), "pack": (8, 24), "dec_navidad": 1.45,
    },
}

CIUDADES = [
    ("Puerto Claro", "Litoral"), ("Valle Verde", "Centro"), ("San Marcos", "Centro"),
    ("Costa Azul", "Litoral"), ("Alto Molino", "Norte"), ("La Ribera", "Sur"),
    ("Monte Sereno", "Norte"), ("Campo Nuevo", "Sur"), ("Bahía Norte", "Litoral"),
    ("El Mirador", "Centro"), ("Villa Esperanza", "Sur"), ("Paso Real", "Norte"),
]

NOMBRES_PROVEEDORES = [
    "Distribuidora Andina", "Comercial del Sur", "Alimentos Cumbre", "Logística Pacífico",
    "Proveedora Central", "Agroindustrial Verde", "Importadora Horizonte", "Frutícola Río Claro",
    "Cárnicos del Valle", "Lácteos La Pradera", "Bebidas del Litoral", "Panificadora Sol",
    "Congelados Mar Azul", "Suministros Limpios", "Higiene Total", "Snacks del Monte",
    "Mayorista El Roble", "Transportes Norte", "Bodega San Marcos", "Comercial Bahía",
    "Alimentos del Paso", "Distribuidora Esperanza", "Productos del Campo", "Cadena Fría Sur",
    "Abarrotes Unidos", "Conservas del Puerto", "Molinos Centrales", "Viñedos de Altura",
    "Ganadería Serrana", "Huertos del Mirador", "Dulces Tradición", "Papelera Andina",
    "Química del Hogar", "Cosmética Natural", "Frutos Selectos", "Gourmet Express",
]


def feriados(anio: int) -> list[tuple[dt.date, str]]:
    """Feriados ficticios de tipo latinoamericano, representativos y genericos."""
    pascua = _domingo_pascua(anio)
    jueves_santo = pascua - dt.timedelta(days=3)
    viernes_santo = pascua - dt.timedelta(days=2)
    carnaval = pascua - dt.timedelta(days=48)
    dia_madre = _n_esimo_domingo(anio, 5, 2)
    dia_padre = _n_esimo_domingo(anio, 6, 3)
    dia_nino = _n_esimo_domingo(anio, 8, 3)
    return [
        (dt.date(anio, 1, 1), "Año Nuevo"),
        (carnaval, "Carnaval"),
        (jueves_santo, "Jueves Santo"),
        (viernes_santo, "Viernes Santo"),
        (dt.date(anio, 5, 1), "Día del Trabajador"),
        (dia_madre, "Día de la Madre"),
        (dia_padre, "Día del Padre"),
        (dia_nino, "Día del Niño"),
        (dt.date(anio, 9, 18), "Fiestas Patrias"),
        (dt.date(anio, 9, 19), "Fiestas Patrias"),
        (dt.date(anio, 12, 24), "Nochebuena"),
        (dt.date(anio, 12, 25), "Navidad"),
        (dt.date(anio, 12, 31), "Fin de Año"),
    ]


def _domingo_pascua(anio: int) -> dt.date:
    """Algoritmo de Gauss-Meeus para el domingo de Pascua."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    mes = (h + l_ - 7 * m + 114) // 31
    dia = ((h + l_ - 7 * m + 114) % 31) + 1
    return dt.date(anio, mes, dia)


def _n_esimo_domingo(anio: int, mes: int, n: int) -> dt.date:
    dia = dt.date(anio, mes, 1)
    offset = (6 - dia.weekday()) % 7
    return dia + dt.timedelta(days=offset + 7 * (n - 1))
