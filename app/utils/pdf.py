"""
Generación de PDFs con WeasyPrint.

Las llamadas a WeasyPrint están encapsuladas en try/except para que la
aplicación pueda arrancar incluso si las dependencias del sistema no están
disponibles (WeasyPrint requiere librerías nativas Cairo/Pango/GObject).
En ese caso se devuelve un HTML descargable como fallback.
"""
import re
from flask import render_template, current_app


# --- HELPERS DE FORMATO ---

def _formato_moneda_co(valor):
    """Formato colombiano: 1.234.567,89 (sin símbolo)."""
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        valor = 0.0
    entero, decimal = f"{valor:,.2f}".split(".")
    entero = entero.replace(",", ".")
    return f"{entero},{decimal}"


def _numero_a_letras(valor):
    """Convierte número a letras en español colombiano. P.ej.: 'TRESCIENTOS MIL PESOS'."""
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        valor = 0.0

    try:
        from num2words import num2words
        entero = int(valor)
        decimales = int(round((valor - entero) * 100))
        texto = num2words(entero, lang="es")
        resultado = texto.upper()
        if decimales > 0:
            cents = num2words(decimales, lang="es").upper()
            resultado = f"{resultado} PESOS CON {cents} CENTAVOS"
        else:
            resultado = f"{resultado} PESOS"
        return resultado
    except Exception as exc:
        current_app.logger.warning(f"No se pudo convertir a letras: {exc}")
        return f"{int(valor):,} PESOS".replace(",", ".")


# --- WEASYPRINT ---

def _intentar_weasyprint(html):
    """Intenta convertir HTML a PDF con WeasyPrint; devuelve bytes o None."""
    try:
        from weasyprint import HTML  # import perezoso
        return HTML(string=html, base_url=current_app.root_path).write_pdf()
    except Exception as exc:
        current_app.logger.warning(f"WeasyPrint no disponible: {exc}")
        return None


# --- GENERADORES POR TIPO ---

def generar_pdf_cotizacion(cotizacion, plantilla=None):
    """Devuelve una tupla (contenido_bytes, content_type, extension)."""
    if plantilla and plantilla.html_contenido:
        html = _renderizar_plantilla_personalizada(plantilla, cotizacion=cotizacion)
    else:
        html = render_template("pdf/cotizacion.html", cotizacion=cotizacion)

    pdf = _intentar_weasyprint(html)
    if pdf:
        return pdf, "application/pdf", "pdf"
    return html.encode("utf-8"), "text/html; charset=utf-8", "html"


def generar_pdf_cuenta_cobro(cuenta, plantilla=None):
    if plantilla and plantilla.html_contenido:
        html = _renderizar_plantilla_personalizada(plantilla, cuenta=cuenta)
    else:
        html = render_template("pdf/cuenta_cobro.html", cuenta=cuenta)

    pdf = _intentar_weasyprint(html)
    if pdf:
        return pdf, "application/pdf", "pdf"
    return html.encode("utf-8"), "text/html; charset=utf-8", "html"


# --- RENDERIZADOR DE PLANTILLAS PERSONALIZADAS ---

def _renderizar_plantilla_personalizada(plantilla, **contexto):
    """
    Renderiza una plantilla personalizada del Layout Designer.

    Hace una sustitución case-insensitive de marcadores tipo {{variable}}.
    Es conservador para no ejecutar Jinja arbitrario en HTML de GrapesJS.

    Reglas:
      - {{VARIABLE}}, {{variable}} y {{Variable}} se reemplazan por igual.
      - El HTML resultante siempre incluye charset UTF-8.
    """
    cotizacion = contexto.get("cotizacion")
    cuenta = contexto.get("cuenta")

    reemplazos = {}

    if cotizacion:
        valor_total = float(cotizacion.total or 0)
        reemplazos.update({
            "numero": cotizacion.numero or "",
            "fecha": cotizacion.fecha.strftime("%d/%m/%Y") if cotizacion.fecha else "",
            "cliente_nombre": cotizacion.cliente.nombre if cotizacion.cliente else "",
            "cliente_nit": (cotizacion.cliente.nit or "") if cotizacion.cliente else "",
            "cliente_direccion": (cotizacion.cliente.direccion or "") if cotizacion.cliente else "",
            "cliente_telefono": (cotizacion.cliente.telefono or "") if cotizacion.cliente else "",
            "cliente_correo": (cotizacion.cliente.correo or "") if cotizacion.cliente else "",
            "observaciones": cotizacion.observaciones or "",
            "subtotal": _formato_moneda_co(cotizacion.subtotal),
            "iva_total": _formato_moneda_co(cotizacion.iva_total),
            "total": _formato_moneda_co(cotizacion.total),
            "valor": _formato_moneda_co(cotizacion.total),
            "valor_letras": _numero_a_letras(valor_total),
            "empresa_nombre": cotizacion.empresa.nombre if cotizacion.empresa else "",
            "empresa_nit": cotizacion.empresa.nit if cotizacion.empresa else "",
            "empresa_direccion": (cotizacion.empresa.direccion or "") if cotizacion.empresa else "",
            "empresa_telefono": (cotizacion.empresa.telefono or "") if cotizacion.empresa else "",
            "empresa_correo": (cotizacion.empresa.correo or "") if cotizacion.empresa else "",
        })

    if cuenta:
        valor_total = float(cuenta.valor or 0)
        emp = cuenta.empresa

        # === Procesar concepto: quitar línea "Servicios según cotización ..."
        # y agregar observaciones de la cotización al final (si existen) ===
        concepto_original = cuenta.concepto or ""
        lineas = concepto_original.split("\n")
        # Si la primera línea es la de "Servicios según cotización COT-XXX:", la quitamos
        if lineas and lineas[0].strip().lower().startswith("servicios según cotización"):
            lineas = lineas[1:]
        concepto_items = "\n".join(lineas).strip()

        # Agregar observaciones si vienen de una cotización vinculada
        if cuenta.cotizacion and cuenta.cotizacion.observaciones:
            obs = cuenta.cotizacion.observaciones.strip()
            if obs:
                concepto_items = (concepto_items + "\n\n" + obs).strip() if concepto_items else obs

        # === Firma dinámica ===
        # Carga la firma desde el archivo subido por la empresa.
        # Si no hay firma cargada, deja la celda vacía (solo línea + label).
        firma_html = ""
        if emp and emp.firma:
            try:
                from app.utils.plantilla_azul import _firma_data_uri
                firma_uri = _firma_data_uri(emp)
                if firma_uri:
                    firma_html = (
                        f'<div class="caz-firma-contenedor">'
                        f'<img src="{firma_uri}" alt="Firma" class="caz-firma-img">'
                        f'</div>'
                    )
            except Exception as e:
                # current_app ya está disponible a nivel de módulo
                try:
                    current_app.logger.warning(f"No se pudo cargar firma de empresa: {e}")
                except Exception:
                    pass

        reemplazos.update({
            "consecutivo": cuenta.consecutivo or "",
            "numero": cuenta.consecutivo or "",
            "fecha": cuenta.fecha.strftime("%d/%m/%Y") if cuenta.fecha else "",
            "cliente_nombre": cuenta.cliente.nombre if cuenta.cliente else "",
            "cliente_nit": (cuenta.cliente.nit or "") if cuenta.cliente else "",
            "cliente_direccion": (cuenta.cliente.direccion or "") if cuenta.cliente else "",
            "cliente_telefono": (cuenta.cliente.telefono or "") if cuenta.cliente else "",
            "cliente_correo": (cuenta.cliente.correo or "") if cuenta.cliente else "",
            "concepto": cuenta.concepto or "",
            "concepto_items": concepto_items,   # versión sin cabecera + con observaciones
            "firma_html": firma_html,           # HTML de la firma (vacío si no hay)
            "valor": _formato_moneda_co(cuenta.valor),
            "total": _formato_moneda_co(cuenta.valor),
            "valor_letras": _numero_a_letras(valor_total),
            "empresa_nombre": emp.nombre if emp else "",
            "empresa_nit": emp.nit if emp else "",
            "empresa_direccion": (emp.direccion or "") if emp else "",
            "empresa_telefono": (emp.telefono or "") if emp else "",
            "empresa_correo": (emp.correo or "") if emp else "",
            # Métodos de pago configurables desde el form de empresa
            "pago_llave": (emp.pago_llave or "") if emp else "",
            "pago_daviplata": (emp.pago_daviplata or "") if emp else "",
            "pago_nequi": (emp.pago_nequi or "") if emp else "",
            "pago_extra_label": (emp.pago_extra_label or "") if emp else "",
            "pago_extra_valor": (emp.pago_extra_valor or "") if emp else "",
        })

    cuerpo = (plantilla.html_contenido or "")
    css = (plantilla.css_contenido or "")

    # Sustitución case-insensitive de {{variable}}
    def _sustituir(match):
        clave = match.group(1).strip().lower()
        return str(reemplazos.get(clave, match.group(0)))

    patron = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
    cuerpo = patron.sub(_sustituir, cuerpo)
    css = patron.sub(_sustituir, css)

    # Determinar qué tipografía usar (la configurada en la empresa)
    import os
    from app.utils.tipografias import obtener_tipografia, font_face_block, stack_css, TIPOGRAFIA_DEFAULT

    empresa = (cotizacion.empresa if cotizacion
               else cuenta.empresa if cuenta
               else None)
    id_tipo = (empresa.tipografia if empresa and empresa.tipografia
               else TIPOGRAFIA_DEFAULT)
    tipo = obtener_tipografia(id_tipo)

    # Ruta absoluta a la carpeta de fuentes para que WeasyPrint las embeba en el PDF
    font_dir = os.path.join(current_app.root_path, "static", "fonts")
    font_base_url = f"file://{font_dir}/"

    font_face_css = font_face_block(id_tipo, base_url=font_base_url)
    font_family_stack = stack_css(id_tipo)

    html_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>{plantilla.nombre}</title>
<style>
/* Tipografía configurada en la empresa: {tipo['nombre']} */
{font_face_css}

/* @page por defecto - puede ser sobreescrito por el CSS de la plantilla */
@page {{ size: A4; margin: 1cm; }}
body {{
  font-family: {font_family_stack};
  margin: 0;
  padding: 0;
}}
/* CSS de la plantilla (sobreescribe lo anterior si lo redefine) */
{css}
</style>
</head>
<body>
{cuerpo}
</body>
</html>"""
    return html_final
