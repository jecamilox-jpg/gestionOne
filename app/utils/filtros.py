"""
Filtros Jinja personalizados.
"""
from datetime import datetime


def moneda(valor, simbolo="$"):
    """Formatea un número como moneda colombiana: $ 1.234.567,89"""
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        valor = 0.0
    entero, decimal = f"{valor:,.2f}".split(".")
    entero = entero.replace(",", ".")
    return f"{simbolo} {entero},{decimal}"


def fecha_es(valor, formato="%d/%m/%Y"):
    """Formatea una fecha en formato latino."""
    if not valor:
        return ""
    if isinstance(valor, str):
        try:
            valor = datetime.fromisoformat(valor)
        except ValueError:
            return valor
    return valor.strftime(formato)


def badge_estado(estado):
    """Devuelve clase Bootstrap para un estado."""
    mapping = {
        "activo": "success",
        "inactivo": "secondary",
        "borrador": "secondary",
        "aprobada": "success",
        "anulada": "danger",
        "pendiente": "warning",
        "pagada": "success",
    }
    return mapping.get((estado or "").lower(), "secondary")


def registrar(app):
    """Registra todos los filtros en la app."""
    app.jinja_env.filters["moneda"] = moneda
    app.jinja_env.filters["fecha_es"] = fecha_es
    app.jinja_env.filters["badge_estado"] = badge_estado
