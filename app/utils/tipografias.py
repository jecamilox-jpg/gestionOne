"""
Catálogo de tipografías disponibles en GestiónOne.

Cada entrada define:
  - id: clave guardada en BD
  - nombre: etiqueta humana mostrada en formularios
  - descripcion: contexto donde encaja mejor
  - archivo: nombre del .ttf en app/static/fonts/
  - stack_css: lista de familias para el CSS, en orden de preferencia
  - locales: nombres "local()" para que el navegador use la versión
             instalada en el sistema si existe (mucho más eficiente)
"""

TIPOGRAFIAS = {
    "century_gothic": {
        "nombre": "Century Gothic",
        "descripcion": "Geométrica y elegante. Ideal para documentos formales (facturas, cuentas de cobro).",
        "archivo": "Questrial-Regular.ttf",
        "stack_css": ['"Century Gothic"', '"URW Gothic"', '"Avant Garde"', '"Trebuchet MS"', 'sans-serif'],
        "locales": ['"Century Gothic"', '"URW Gothic"', '"AvantGarde-Book"'],
    },
    "inter": {
        "nombre": "Inter",
        "descripcion": "Moderna y nítida. La fuente típica de apps SaaS (GitHub, Figma, Mozilla).",
        "archivo": "Inter-Regular.ttf",
        "stack_css": ['"Inter"', '"Segoe UI"', 'system-ui', '-apple-system', 'sans-serif'],
        "locales": ['"Inter"'],
    },
    "roboto": {
        "nombre": "Roboto",
        "descripcion": "Neutra y muy legible. Es la fuente oficial de Google y Android.",
        "archivo": "Roboto-Regular.ttf",
        "stack_css": ['"Roboto"', '"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
        "locales": ['"Roboto"'],
    },
    "poppins": {
        "nombre": "Poppins",
        "descripcion": "Geométrica amigable y redondeada. Da un toque cálido y moderno.",
        "archivo": "Poppins-Regular.ttf",
        "stack_css": ['"Poppins"', '"Futura"', '"Trebuchet MS"', 'sans-serif'],
        "locales": ['"Poppins"'],
    },
    "lato": {
        "nombre": "Lato",
        "descripcion": "Humanista y cálida. Perfecta para texto largo y comunicaciones profesionales.",
        "archivo": "Lato-Regular.ttf",
        "stack_css": ['"Lato"', '"Lucida Sans"', '"Trebuchet MS"', 'sans-serif'],
        "locales": ['"Lato"'],
    },
    "open_sans": {
        "nombre": "Open Sans",
        "descripcion": "Clásica, segura y neutral. Una de las fuentes más usadas en la web.",
        "archivo": "OpenSans-Regular.ttf",
        "stack_css": ['"Open Sans"', '"Segoe UI"', 'Tahoma', 'sans-serif'],
        "locales": ['"Open Sans"'],
    },
}

# Default si no se encuentra la clave guardada o la empresa no tiene una asignada
TIPOGRAFIA_DEFAULT = "century_gothic"


def obtener_tipografia(id_tipografia):
    """Devuelve el dict de la tipografía. Si no existe, devuelve la default."""
    return TIPOGRAFIAS.get(id_tipografia) or TIPOGRAFIAS[TIPOGRAFIA_DEFAULT]


def stack_css(id_tipografia):
    """Devuelve la stack CSS como string: '"Inter", "Segoe UI", ...'."""
    tipo = obtener_tipografia(id_tipografia)
    return ", ".join(tipo["stack_css"])


def font_face_block(id_tipografia, base_url=""):
    """
    Genera un bloque @font-face para WeasyPrint o el navegador.

    base_url: prefijo para la URL de la fuente.
      - Para WeasyPrint: 'file:///ruta/absoluta/al/static/fonts/'
      - Para el navegador: '/static/fonts/'
    """
    tipo = obtener_tipografia(id_tipografia)
    familia_principal = tipo["stack_css"][0]   # ej: '"Century Gothic"'
    locales = ", ".join(f"local({l})" for l in tipo["locales"])
    src = f"{locales}, url(\"{base_url}{tipo['archivo']}\") format(\"truetype\")"

    return (
        "@font-face {\n"
        f"  font-family: {familia_principal};\n"
        f"  src: {src};\n"
        "  font-weight: normal;\n"
        "  font-style: normal;\n"
        "  font-display: swap;\n"
        "}\n"
        "@font-face {\n"
        f"  font-family: {familia_principal};\n"
        f"  src: {src};\n"
        "  font-weight: bold;\n"
        "  font-style: normal;\n"
        "}\n"
    )
