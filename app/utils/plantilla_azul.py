"""
Instalador de la plantilla 'Cuenta de cobro — Estilo Azul'.

Diseño moderno tipo factura SaaS, en color azul/morado, similar al diseño
de cotizaciones. La firma se carga dinámicamente desde la empresa (campo
empresa.firma). Si la empresa no tiene firma cargada, se omite la imagen
y solo se muestra la línea para firmar.
"""
import base64
import os
import logging

logger = logging.getLogger(__name__)


def _firma_data_uri(empresa=None):
    """
    Devuelve la firma como data URI base64 leyendo el archivo subido por la empresa.
    Si la empresa no tiene firma cargada, devuelve cadena vacía.
    """
    if not empresa or not empresa.firma:
        return ""
    # Buscar el archivo en uploads (configurable por env)
    base = os.environ.get("UPLOAD_FOLDER") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "uploads"
    )
    firma_path = os.path.join(base, empresa.firma)
    if not os.path.exists(firma_path):
        logger.warning(f"Firma de empresa no encontrada en {firma_path}")
        return ""
    # Detectar mime type
    ext = empresa.firma.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")
    with open(firma_path, "rb") as f:
        firma_b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{firma_b64}"


def _build_html():
    """HTML de la plantilla. La firma se sustituye en runtime vía variable {{firma_uri}}."""
    return """<div class="caz-doc">

  <!-- Cabecera: emisor (izq) + título y número (der) -->
  <table class="caz-cabecera">
    <tr>
      <td class="caz-emisor">
        <div class="caz-emisor-nombre">{{empresa_nombre}}</div>
        <div class="caz-emisor-linea">CC: {{empresa_nit}}</div>
        <div class="caz-emisor-linea">{{empresa_direccion}}</div>
        <div class="caz-emisor-linea">Tel: {{empresa_telefono}} · {{empresa_correo}}</div>
      </td>
      <td class="caz-doc-info">
        <div class="caz-titulo">CUENTA DE COBRO</div>
        <div class="caz-numero">{{consecutivo}}</div>
        <div class="caz-fecha-linea">Fecha: {{fecha}}</div>
      </td>
    </tr>
  </table>

  <hr class="caz-divisor">

  <!-- Cards: Cliente + Detalles del documento -->
  <table class="caz-cards">
    <tr>
      <td class="caz-card">
        <div class="caz-card-label">CLIENTE</div>
        <div class="caz-card-nombre">{{cliente_nombre}}</div>
        <div class="caz-card-linea">NIT: {{cliente_nit}}</div>
        <div class="caz-card-linea">{{cliente_direccion}}</div>
        <div class="caz-card-linea">Tel: {{cliente_telefono}}</div>
        <div class="caz-card-linea">{{cliente_correo}}</div>
      </td>
      <td class="caz-card">
        <div class="caz-card-label">DETALLES DEL DOCUMENTO</div>
        <div class="caz-card-linea">Número:</div>
        <div class="caz-card-nombre">{{consecutivo}}</div>
        <div class="caz-card-linea">Fecha emisión: {{fecha}}</div>
      </td>
    </tr>
  </table>

  <!-- Tabla de concepto -->
  <table class="caz-tabla-items">
    <thead>
      <tr>
        <th class="caz-th-desc">Descripción</th>
        <th class="caz-th-num">Cantidad</th>
        <th class="caz-th-num">Valor unit.</th>
        <th class="caz-th-num">Total</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="caz-td-desc">{{concepto_items}}</td>
        <td class="caz-td-num">1</td>
        <td class="caz-td-num">$ {{valor}}</td>
        <td class="caz-td-num">$ {{valor}}</td>
      </tr>
    </tbody>
  </table>

  <!-- Totales -->
  <table class="caz-totales">
    <tr>
      <td class="caz-totales-spacer"></td>
      <td class="caz-totales-box">
        <table class="caz-totales-tabla">
          <tr>
            <td class="caz-total-label">Subtotal</td>
            <td class="caz-total-valor">$ {{valor}}</td>
          </tr>
          <tr>
            <td class="caz-total-label">IVA</td>
            <td class="caz-total-valor">$ 0</td>
          </tr>
          <tr class="caz-total-final">
            <td class="caz-total-label">Total</td>
            <td class="caz-total-valor">$ {{valor}}</td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- SON en letras -->
  <div class="caz-son">
    <span class="caz-son-label">SON:</span>
    <span class="caz-son-valor">{{valor_letras}}</span>
  </div>

  <!-- Métodos de pago -->
  <div class="caz-pagos-titulo">MÉTODOS DE PAGO</div>
  <table class="caz-pagos">
    <tr>
      <td class="caz-pago-label">Llave</td>
      <td class="caz-pago-valor">{{pago_llave}}</td>
      <td class="caz-pago-label">Daviplata</td>
      <td class="caz-pago-valor">{{pago_daviplata}}</td>
      <td class="caz-pago-label">Nequi</td>
      <td class="caz-pago-valor">{{pago_nequi}}</td>
    </tr>
  </table>

  <!-- Firma + nota legal -->
  <table class="caz-firma-zona">
    <tr>
      <td class="caz-firma-cell">
        {{firma_html}}
        <div class="caz-firma-linea"></div>
        <div class="caz-firma-label">FIRMA</div>
      </td>
      <td class="caz-nota-cell">
        <div class="caz-nota-titulo">NOTA</div>
        <p class="caz-nota">
          Certifico que el servicio lo presté de manera personal y para
          desarrollar esta actividad no vínculo más de dos personas, me acojo al
          artículo 8383 de la ley 1819 de diciembre de 2016 para efectos tributarios.
        </p>
      </td>
    </tr>
  </table>

</div>
"""


CSS_PLANTILLA = """
@page { size: A4; margin: 1.4cm 1.5cm; }
* { box-sizing: border-box; }
body { margin: 0; padding: 0; color: #1f2937; }

.caz-doc {
  font-size: 10.5px;
  color: #1f2937;
  line-height: 1.4;
}

/* === Cabecera === */
.caz-cabecera { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
.caz-emisor { width: 60%; vertical-align: top; padding: 0; }
.caz-emisor-nombre {
  color: #635bff;
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
}
.caz-emisor-linea { color: #6b7280; font-size: 10px; line-height: 1.5; }

.caz-doc-info { width: 40%; vertical-align: top; text-align: right; }
.caz-titulo {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.5px;
  color: #1f2937;
  margin-bottom: 4px;
}
.caz-numero {
  font-size: 13px;
  color: #635bff;
  font-weight: 600;
  margin-bottom: 6px;
}
.caz-fecha-linea { color: #6b7280; font-size: 10px; line-height: 1.5; }

.caz-divisor { border: none; border-top: 1.5px solid #e5e7eb; margin: 12px 0 16px; }

/* === Cards === */
.caz-cards { width: 100%; border-collapse: separate; border-spacing: 12px 0; margin-bottom: 18px; }
.caz-card {
  width: 50%;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 14px;
  vertical-align: top;
}
.caz-card-label {
  font-size: 9px; font-weight: 700; color: #6b7280;
  letter-spacing: 1px; margin-bottom: 6px;
}
.caz-card-nombre {
  font-size: 12px; font-weight: 700; color: #1f2937; margin: 2px 0;
}
.caz-card-linea { font-size: 10px; color: #4b5563; line-height: 1.5; }

/* === Tabla items === */
.caz-tabla-items { width: 100%; border-collapse: collapse; }
.caz-tabla-items thead th {
  background: #635bff; color: #fff;
  font-weight: 600; font-size: 10px;
  padding: 9px 12px; text-align: left; letter-spacing: 0.3px;
}
.caz-th-desc { width: 50%; }
.caz-th-num { text-align: right !important; width: 16.6%; }
.caz-tabla-items tbody td {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 10.5px;
  vertical-align: top;
}
.caz-td-desc { white-space: pre-line; line-height: 1.55; }
.caz-td-num { text-align: right; white-space: nowrap; }

/* === Totales === */
.caz-totales { width: 100%; border-collapse: collapse; margin-top: -1px; margin-bottom: 14px; }
.caz-totales-spacer { width: 55%; }
.caz-totales-box { width: 45%; padding: 0; }
.caz-totales-tabla {
  width: 100%; border-collapse: collapse;
  background: #f9fafb;
  border: 1px solid #e5e7eb; border-radius: 6px;
}
.caz-totales-tabla td { padding: 8px 14px; font-size: 10.5px; }
.caz-total-label { color: #4b5563; }
.caz-total-valor { text-align: right; font-weight: 600; color: #1f2937; }
.caz-total-final td {
  background: #635bff; color: #fff !important;
  font-size: 12px; font-weight: 700;
}
.caz-total-final .caz-total-label, .caz-total-final .caz-total-valor { color: #fff; }

/* === SON === */
.caz-son {
  background: #f9fafb;
  border-left: 4px solid #635bff;
  padding: 8px 12px;
  margin-bottom: 16px;
  font-size: 10px;
}
.caz-son-label { font-weight: 700; color: #635bff; margin-right: 6px; }
.caz-son-valor {
  font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.3px; color: #1f2937;
}

/* === Métodos de pago === */
.caz-pagos-titulo {
  font-size: 9px; font-weight: 700; color: #6b7280;
  letter-spacing: 1px; margin-bottom: 6px;
}
.caz-pagos {
  width: 100%; border-collapse: collapse;
  margin-bottom: 22px;
  background: #f9fafb;
  border: 1px solid #e5e7eb; border-radius: 6px;
}
.caz-pagos td {
  padding: 8px 12px; font-size: 10px;
  border-right: 1px solid #e5e7eb;
}
.caz-pagos td:last-child { border-right: none; }
.caz-pago-label { font-weight: 600; color: #6b7280; width: 12%; }
.caz-pago-valor { font-weight: 600; color: #1f2937; width: 21.3%; }

/* === Firma y nota === */
.caz-firma-zona { width: 100%; border-collapse: collapse; margin-top: 8px; }
.caz-firma-cell {
  width: 45%; vertical-align: top;
  text-align: center; padding: 8px 16px;
}
.caz-firma-contenedor {
  /* Caja que limita el tamaño máximo de la firma para que no se deforme */
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}
.caz-firma-img {
  /* object-fit mantiene la proporción original sin estirar la imagen */
  max-width: 180px;
  max-height: 60px;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
}
.caz-firma-linea {
  border-top: 1px solid #1f2937;
  width: 70%;
  margin: 4px auto 6px;
}
.caz-firma-label {
  font-size: 9px; font-weight: 700;
  letter-spacing: 2px; color: #4b5563;
}

.caz-nota-cell {
  width: 55%; vertical-align: top;
  padding: 8px 0 8px 16px;
  border-left: 3px solid #e5e7eb;
}
.caz-nota-titulo {
  font-size: 9px; font-weight: 700; color: #6b7280;
  letter-spacing: 1.2px; margin-bottom: 4px;
}
.caz-nota {
  margin: 0; font-size: 9.5px; line-height: 1.5;
  color: #4b5563; text-align: justify;
}
"""


def instalar_plantilla_azul(empresa=None):
    """
    Crea o actualiza la plantilla 'Cuenta de cobro — Estilo Azul'.
    La firma se carga DINÁMICAMENTE en cada generación de PDF leyendo
    empresa.firma. Si no hay firma, solo se muestra la línea para firmar a mano.
    """
    from app import db
    from app.models import PlantillaLayout, Empresa

    if empresa is None:
        empresa = Empresa.query.first()
    if empresa is None:
        logger.warning("instalar_plantilla_azul: no hay empresas en la BD")
        return None

    html_contenido = _build_html()

    existing = PlantillaLayout.query.filter_by(
        nombre="Cuenta de cobro — Estilo Azul",
        tipo="cuenta_cobro",
        empresa_id=empresa.id,
    ).first()

    if existing:
        existing.html_contenido = html_contenido
        existing.css_contenido = CSS_PLANTILLA
        existing.componentes_json = "[]"
        existing.estilos_json = "[]"
        plantilla = existing
        logger.info(f"Plantilla 'Estilo Azul' actualizada (id={plantilla.id})")
    else:
        plantilla = PlantillaLayout(
            nombre="Cuenta de cobro — Estilo Azul",
            tipo="cuenta_cobro",
            html_contenido=html_contenido,
            css_contenido=CSS_PLANTILLA,
            componentes_json="[]",
            estilos_json="[]",
            es_predeterminada=False,
            empresa_id=empresa.id,
        )
        db.session.add(plantilla)
        db.session.flush()
        logger.info(f"Plantilla 'Estilo Azul' creada (id={plantilla.id})")

    db.session.commit()
    return plantilla
