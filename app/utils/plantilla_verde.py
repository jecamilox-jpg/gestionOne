"""
Instalador de la plantilla 'Cuenta de cobro — Estilo Verde'.

Este módulo expone una función `instalar_plantilla_verde()` que crea (o actualiza)
la plantilla predeterminada de cuentas de cobro en la base de datos.

Se invoca automáticamente en la inicialización de la app (wsgi.py), pero también
puede ejecutarse manualmente con: python crear_plantilla_verde.py
"""
import base64
import os
import logging

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Recursos estáticos: firma del usuario incrustada en base64
# ----------------------------------------------------------------------------

def _firma_data_uri():
    """Lee la firma del disco y la devuelve como data URI base64."""
    firma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # app/
        "static", "img", "firma.png"
    )
    if not os.path.exists(firma_path):
        logger.warning(f"Firma no encontrada en {firma_path}, se omite imagen")
        return ""
    with open(firma_path, "rb") as f:
        firma_b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{firma_b64}"


# ----------------------------------------------------------------------------
# Plantilla HTML — todo el cuerpo del documento
# ----------------------------------------------------------------------------

def _build_html(firma_uri):
    """Construye el HTML de la plantilla con la firma ya embebida."""
    return f"""<div class="cdc-doc">
  <!-- Encabezado verde -->
  <div class="cdc-header">
    <div class="cdc-header-left">Cuenta de cobro</div>
    <div class="cdc-header-right">
      <span class="cdc-header-label">FECHA</span>
      <span class="cdc-header-value">{{{{fecha}}}}</span>
    </div>
  </div>

  <!-- Datos del cliente -->
  <table class="cdc-tabla cdc-cliente">
    <tr>
      <td class="cdc-label">CLIENTE</td>
      <td class="cdc-valor">{{{{cliente_nombre}}}}</td>
      <td class="cdc-label">NIT</td>
      <td class="cdc-valor">{{{{cliente_nit}}}}</td>
    </tr>
    <tr>
      <td class="cdc-label">DEBE A</td>
      <td class="cdc-valor">{{{{empresa_nombre}}}}</td>
      <td class="cdc-label">C.C</td>
      <td class="cdc-valor">{{{{empresa_nit}}}}</td>
    </tr>
  </table>

  <!-- Tabla de concepto -->
  <table class="cdc-tabla cdc-concepto">
    <thead>
      <tr>
        <th class="col-concepto">POR CONCEPTO DE</th>
        <th class="col-cantidad">CANTIDAD</th>
        <th class="col-unitario">VALOR UNITARIO</th>
        <th class="col-total">VALOR TOTAL</th>
      </tr>
    </thead>
    <tbody>
      <tr class="cdc-fila-concepto">
        <td class="cdc-concepto-celda">{{{{concepto}}}}</td>
        <td class="text-center">1</td>
        <td class="text-right">$ {{{{valor}}}}</td>
        <td class="text-right">$ {{{{valor}}}}</td>
      </tr>
    </tbody>
  </table>

  <!-- Métodos de pago -->
  <table class="cdc-tabla cdc-pagos">
    <tr>
      <td class="cdc-pago-label">LLAVE</td>
      <td class="cdc-pago-valor">{{{{pago_llave}}}}</td>
      <td rowspan="3" class="cdc-pago-spacer"></td>
    </tr>
    <tr>
      <td class="cdc-pago-label">DAVIPLATA</td>
      <td class="cdc-pago-valor">{{{{pago_daviplata}}}}</td>
    </tr>
    <tr>
      <td class="cdc-pago-label">NEQUI</td>
      <td class="cdc-pago-valor">{{{{pago_nequi}}}}</td>
    </tr>
  </table>

  <!-- SON y TOTAL -->
  <table class="cdc-tabla cdc-total">
    <tr>
      <td class="cdc-son-label">SON:</td>
      <td class="cdc-son-valor">{{{{valor_letras}}}}</td>
      <td class="cdc-total-label">TOTAL</td>
      <td class="cdc-total-valor">$ {{{{valor}}}}</td>
    </tr>
  </table>

  <!-- Firma y nota regulatoria -->
  <table class="cdc-tabla cdc-firma-zona">
    <tr>
      <td class="cdc-firma-cell">
        <img src="{firma_uri}" alt="Firma" class="cdc-firma-img">
        <div class="cdc-firma-label">FIRMA</div>
      </td>
      <td class="cdc-nota-cell">
        <p class="cdc-nota">
          NOTA: Certifico que el servicio lo presté de manera personal y para
          desarrollar esta actividad no vínculo más de dos personas, me acojo al
          artículo 8383 de la ley 1819 de diciembre de 2016 para efectos tributarios
        </p>
      </td>
    </tr>
  </table>
</div>
"""


# ----------------------------------------------------------------------------
# CSS optimizado para A5 vertical
# ----------------------------------------------------------------------------

CSS_PLANTILLA = """
@page {
  size: A5;
  margin: 0.6cm 0.7cm;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 0;
  /* font-family: hereda del body (configurable por empresa) */
}

.cdc-doc {
  /* font-family: hereda del body (configurable por empresa) */
  color: #222;
  font-size: 9.5px;
  width: 100%;
  max-width: 14cm;
  margin: 0 auto;
  border: 1.5px solid #000;
}

/* Encabezado verde */
.cdc-header {
  background: #2eb24a;
  color: #fff;
  font-weight: bold;
  display: table;
  width: 100%;
  border-bottom: 1.5px solid #000;
}
.cdc-header-left {
  display: table-cell;
  padding: 6px 10px;
  font-size: 11px;
}
.cdc-header-right {
  display: table-cell;
  text-align: right;
  padding: 6px 10px;
  font-size: 10px;
  white-space: nowrap;
}
.cdc-header-label {
  margin-right: 10px;
  font-weight: bold;
}
.cdc-header-value {
  display: inline-block;
  background: #fff;
  color: #222;
  padding: 2px 8px;
  border-radius: 2px;
  min-width: 70px;
  text-align: center;
  font-weight: bold;
}

/* Tablas generales */
.cdc-tabla {
  width: 100%;
  border-collapse: collapse;
}
.cdc-tabla td,
.cdc-tabla th {
  border: 1px solid #000;
  padding: 4px 8px;
  vertical-align: middle;
}

/* Sección cliente */
.cdc-cliente .cdc-label {
  font-weight: bold;
  background: #fff;
  width: 60px;
  font-size: 9.5px;
}
.cdc-cliente .cdc-valor {
  background: #fff;
}

/* Tabla concepto */
.cdc-concepto thead th {
  background: #fff;
  font-weight: bold;
  text-align: center;
  font-size: 9px;
  padding: 5px 4px;
  letter-spacing: 0.3px;
}
.cdc-concepto .col-concepto { width: 50%; }
.cdc-concepto .col-cantidad { width: 14%; }
.cdc-concepto .col-unitario { width: 18%; }
.cdc-concepto .col-total    { width: 18%; }
.cdc-concepto-celda {
  white-space: pre-line;
  line-height: 1.45;
  padding: 6px 8px !important;
  font-size: 9.5px;
}
.text-center { text-align: center; }
.text-right  { text-align: right; }

/* Sección pagos */
.cdc-pagos td {
  padding: 4px 10px;
  border-top: none;
  border-bottom: none;
  font-size: 9.5px;
}
.cdc-pagos tr:first-child td { border-top: 1px solid #000; }
.cdc-pagos tr:last-child td  { border-bottom: 1px solid #000; }
.cdc-pago-label {
  font-weight: bold;
  width: 80px;
}
.cdc-pago-spacer {
  background: #fff;
}

/* SON y TOTAL */
.cdc-total {
  border-top: 1.5px solid #000;
}
.cdc-total td {
  padding: 5px 8px;
  font-size: 9.5px;
}
.cdc-total .cdc-son-label {
  font-weight: bold;
  width: 40px;
}
.cdc-total .cdc-son-valor {
  text-align: center;
  font-weight: bold;
  text-transform: uppercase;
  font-size: 9px;
}
.cdc-total .cdc-total-label {
  font-weight: bold;
  text-align: center;
  width: 60px;
}
.cdc-total .cdc-total-valor {
  font-weight: bold;
  text-align: right;
  width: 90px;
}

/* Firma y nota */
.cdc-firma-zona td {
  vertical-align: middle;
  padding: 8px;
}
.cdc-firma-cell {
  width: 45%;
  text-align: center;
}
.cdc-firma-img {
  display: block;
  margin: 0 auto 4px;
  height: 50px;
  width: auto;
}
.cdc-firma-label {
  font-size: 8.5px;
  font-weight: bold;
  letter-spacing: 1px;
  color: #444;
  margin-top: 2px;
}
.cdc-nota-cell {
  width: 55%;
}
.cdc-nota {
  margin: 0;
  font-size: 8.5px;
  line-height: 1.35;
  text-align: center;
  color: #333;
}

/* Estilos exclusivos para impresión */
@media print {
  body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .cdc-header, .cdc-header * {
    background: #2eb24a !important;
    color: #fff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .cdc-header-value {
    background: #fff !important;
    color: #222 !important;
  }
}
"""


# ----------------------------------------------------------------------------
# Función pública: idempotente, segura de llamar varias veces
# ----------------------------------------------------------------------------

def instalar_plantilla_verde(empresa=None):
    """
    Crea o actualiza la plantilla 'Cuenta de cobro — Estilo Verde' para una empresa.

    Es idempotente: si la plantilla ya existe la actualiza (no duplica). La marca
    como predeterminada del tipo cuenta_cobro y desmarca las demás.

    Args:
        empresa: instancia de Empresa. Si es None, usa la primera empresa de la BD.

    Returns:
        instancia de PlantillaLayout creada o actualizada.
        None si no hay empresas en la BD.
    """
    from app import db
    from app.models import PlantillaLayout, Empresa

    if empresa is None:
        empresa = Empresa.query.first()

    if empresa is None:
        logger.warning("instalar_plantilla_verde: no hay empresas en la BD, se omite")
        return None

    firma_uri = _firma_data_uri()
    html_contenido = _build_html(firma_uri)

    existing = PlantillaLayout.query.filter_by(
        nombre="Cuenta de cobro — Estilo Verde",
        tipo="cuenta_cobro",
        empresa_id=empresa.id,
    ).first()

    if existing:
        existing.html_contenido = html_contenido
        existing.css_contenido = CSS_PLANTILLA
        existing.componentes_json = "[]"
        existing.estilos_json = "[]"
        plantilla = existing
        logger.info(f"Plantilla 'Estilo Verde' actualizada (id={plantilla.id})")
    else:
        plantilla = PlantillaLayout(
            nombre="Cuenta de cobro — Estilo Verde",
            tipo="cuenta_cobro",
            html_contenido=html_contenido,
            css_contenido=CSS_PLANTILLA,
            componentes_json="[]",
            estilos_json="[]",
            es_predeterminada=True,
            empresa_id=empresa.id,
        )
        db.session.add(plantilla)
        db.session.flush()
        logger.info(f"Plantilla 'Estilo Verde' creada (id={plantilla.id})")

    # Marcar como predeterminada y desmarcar las otras del mismo tipo/empresa
    plantilla.es_predeterminada = True
    PlantillaLayout.query.filter(
        PlantillaLayout.tipo == "cuenta_cobro",
        PlantillaLayout.empresa_id == empresa.id,
        PlantillaLayout.id != plantilla.id,
    ).update({"es_predeterminada": False})

    db.session.commit()
    return plantilla
