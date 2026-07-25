"""
Módulo de cotizaciones.
"""
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, make_response, jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import Cotizacion, DetalleCotizacion, Cliente, Producto, PlantillaLayout
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento
from app.utils.pdf import generar_pdf_cotizacion
from app.utils.correo import enviar_correo

bp = Blueprint("cotizaciones", __name__, template_folder="../../templates/cotizaciones")


def _query_base():
    return Cotizacion.query.filter_by(empresa_id=current_user.empresa_id)


def _siguiente_numero(empresa_id):
    """Genera el siguiente número COT-000001."""
    ultima = (
        Cotizacion.query.filter_by(empresa_id=empresa_id)
        .order_by(Cotizacion.id.desc())
        .first()
    )
    siguiente = (ultima.id + 1) if ultima else 1
    return f"COT-{siguiente:06d}"


# ----------------------------- LISTA ----------------------------- #
@bp.route("/")
@login_required
def lista():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    pagina = int(request.args.get("pagina", 1))

    query = _query_base().join(Cliente)
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(or_(Cotizacion.numero.ilike(like), Cliente.nombre.ilike(like)))
    if estado:
        query = query.filter(Cotizacion.estado == estado)

    paginacion = query.order_by(Cotizacion.creada_en.desc()).paginate(
        page=pagina, per_page=15, error_out=False
    )
    return render_template(
        "cotizaciones/lista.html",
        paginacion=paginacion,
        busqueda=busqueda,
        estado=estado,
    )


# ----------------------------- NUEVA ----------------------------- #
@bp.route("/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nueva():
    if request.method == "POST":
        return _guardar_cotizacion()

    clientes = Cliente.query.filter_by(
        empresa_id=current_user.empresa_id, estado="activo"
    ).order_by(Cliente.nombre).all()
    productos = Producto.query.filter_by(
        empresa_id=current_user.empresa_id, estado="activo"
    ).order_by(Producto.nombre).all()
    return render_template(
        "cotizaciones/form.html",
        cotizacion=None,
        clientes=clientes,
        productos=productos,
    )


# ----------------------------- EDITAR ----------------------------- #
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    if cotizacion.estado == "aprobada":
        flash("Las cotizaciones aprobadas no pueden modificarse.", "warning")
        return redirect(url_for("cotizaciones.detalle", id=id))

    if request.method == "POST":
        return _guardar_cotizacion(cotizacion=cotizacion)

    clientes = Cliente.query.filter_by(empresa_id=current_user.empresa_id).order_by(Cliente.nombre).all()
    productos = Producto.query.filter_by(empresa_id=current_user.empresa_id).order_by(Producto.nombre).all()
    return render_template(
        "cotizaciones/form.html",
        cotizacion=cotizacion,
        clientes=clientes,
        productos=productos,
    )


def _guardar_cotizacion(cotizacion=None):
    """Crea o actualiza una cotización a partir del POST."""
    es_nuevo = cotizacion is None
    if es_nuevo:
        cotizacion = Cotizacion(
            numero=_siguiente_numero(current_user.empresa_id),
            empresa_id=current_user.empresa_id,
            usuario_id=current_user.id,
            estado="borrador",
        )

    cotizacion.cliente_id = int(request.form["cliente_id"])
    cotizacion.fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d").date()
    cotizacion.observaciones = request.form.get("observaciones", "").strip()

    # Reemplaza todos los detalles
    cotizacion.detalles = []
    descripciones = request.form.getlist("descripcion[]")
    productos_ids = request.form.getlist("producto_id[]")
    cantidades = request.form.getlist("cantidad[]")
    precios = request.form.getlist("valor_unitario[]")
    ivas = request.form.getlist("iva[]")

    for i in range(len(descripciones)):
        if not descripciones[i].strip():
            continue
        # Acceso defensivo a cada lista (puede tener distinto tamaño si el form viene incompleto)
        prod_id_raw = productos_ids[i] if i < len(productos_ids) else ""
        cantidad_raw = cantidades[i] if i < len(cantidades) else "0"
        precio_raw = precios[i] if i < len(precios) else "0"
        iva_raw = ivas[i] if i < len(ivas) else "0"

        detalle = DetalleCotizacion(
            descripcion=descripciones[i].strip(),
            producto_id=int(prod_id_raw) if prod_id_raw else None,
            cantidad=float(cantidad_raw or 0),
            valor_unitario=float(precio_raw or 0),
            iva=float(iva_raw or 0),
        )
        cotizacion.detalles.append(detalle)

    cotizacion.recalcular_totales()

    if es_nuevo:
        db.session.add(cotizacion)
    db.session.commit()

    accion = "crear" if es_nuevo else "editar"
    registrar_evento(accion, "cotizaciones", f"Cotización {cotizacion.numero}")
    flash(f"Cotización {cotizacion.numero} guardada.", "success")
    return redirect(url_for("cotizaciones.detalle", id=cotizacion.id))


# ----------------------------- DETALLE ----------------------------- #
@bp.route("/<int:id>")
@login_required
def detalle(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    plantillas = PlantillaLayout.query.filter_by(
        empresa_id=current_user.empresa_id, tipo="cotizacion"
    ).all()
    return render_template(
        "cotizaciones/detalle.html", cotizacion=cotizacion, plantillas=plantillas
    )


# ----------------------------- ACCIONES ----------------------------- #
@bp.route("/<int:id>/aprobar", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def aprobar(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    cotizacion.estado = "aprobada"
    db.session.commit()
    registrar_evento("editar", "cotizaciones", f"Aprobada {cotizacion.numero}")
    flash("Cotización aprobada.", "success")
    return redirect(url_for("cotizaciones.detalle", id=id))


@bp.route("/<int:id>/anular", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def anular(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    cotizacion.estado = "anulada"
    db.session.commit()
    registrar_evento("editar", "cotizaciones", f"Anulada {cotizacion.numero}")
    flash("Cotización anulada.", "warning")
    return redirect(url_for("cotizaciones.detalle", id=id))


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    numero = cotizacion.numero
    db.session.delete(cotizacion)
    db.session.commit()
    registrar_evento("eliminar", "cotizaciones", f"Eliminada {numero}")
    flash("Cotización eliminada.", "success")
    return redirect(url_for("cotizaciones.lista"))


# ----------------------------- PDF ----------------------------- #
@bp.route("/<int:id>/pdf")
@login_required
def pdf(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    plantilla_id = request.args.get("plantilla_id", type=int)
    if plantilla_id:
        plantilla = PlantillaLayout.query.filter_by(
            id=plantilla_id, empresa_id=current_user.empresa_id
        ).first()
    else:
        # Sin plantilla_id: usar la predeterminada de la empresa
        plantilla = PlantillaLayout.query.filter_by(
            tipo="cotizacion",
            empresa_id=current_user.empresa_id,
            es_predeterminada=True,
        ).first()
    contenido, ctype, ext = generar_pdf_cotizacion(cotizacion, plantilla=plantilla)
    response = make_response(contenido)
    response.headers["Content-Type"] = ctype
    response.headers["Content-Disposition"] = (
        f'inline; filename="{cotizacion.numero}.{ext}"'
    )
    registrar_evento("exportar_pdf", "cotizaciones", f"PDF {cotizacion.numero}")
    return response


# ----------------------------- CORREO ----------------------------- #
@bp.route("/<int:id>/enviar", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def enviar(id):
    cotizacion = _query_base().filter_by(id=id).first_or_404()
    destinatario = request.form.get("destinatario", "").strip() or (cotizacion.cliente.correo or "")
    if not destinatario:
        flash("No se especificó un destinatario válido.", "danger")
        return redirect(url_for("cotizaciones.detalle", id=id))

    contenido, ctype, ext = generar_pdf_cotizacion(cotizacion)
    asunto = f"Cotización {cotizacion.numero} - {cotizacion.empresa.nombre}"
    cuerpo = render_template(
        "cotizaciones/correo.html", cotizacion=cotizacion
    )
    ok, mensaje = enviar_correo(
        destinatario, asunto, cuerpo,
        adjuntos=[(f"{cotizacion.numero}.{ext}", contenido, ctype)],
    )
    if ok:
        registrar_evento("enviar_correo", "cotizaciones", f"Enviado {cotizacion.numero} a {destinatario}")
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect(url_for("cotizaciones.detalle", id=id))


# ----------------------------- CONVERTIR A CUENTA ----------------------------- #
@bp.route("/<int:id>/convertir", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def convertir_a_cuenta(id):
    """Convierte una cotización aprobada en cuenta de cobro."""
    from app.models import CuentaCobro

    cotizacion = _query_base().filter_by(id=id).first_or_404()
    if cotizacion.estado != "aprobada":
        flash("Solo las cotizaciones aprobadas se pueden convertir.", "warning")
        return redirect(url_for("cotizaciones.detalle", id=id))

    ultima = (
        CuentaCobro.query.filter_by(empresa_id=current_user.empresa_id)
        .order_by(CuentaCobro.id.desc())
        .first()
    )
    siguiente = (ultima.id + 1) if ultima else 1
    consecutivo = f"CC-{siguiente:06d}"

    # Construir concepto detallado a partir de los items de la cotización
    if cotizacion.detalles:
        lineas = []
        for d in cotizacion.detalles:
            cantidad_str = f"{d.cantidad:g}" if d.cantidad else "1"
            lineas.append(f"• {cantidad_str} x {d.descripcion}")
        concepto_detallado = f"Servicios según cotización {cotizacion.numero}:\n" + "\n".join(lineas)
    else:
        concepto_detallado = f"Servicios según cotización {cotizacion.numero}"

    cuenta = CuentaCobro(
        consecutivo=consecutivo,
        fecha=datetime.utcnow().date(),
        concepto=concepto_detallado,
        valor=cotizacion.total,
        estado="pendiente",
        cliente_id=cotizacion.cliente_id,
        empresa_id=current_user.empresa_id,
        cotizacion_id=cotizacion.id,
        usuario_id=current_user.id,
    )
    db.session.add(cuenta)
    db.session.commit()
    registrar_evento(
        "crear", "cuentas_cobro",
        f"Cuenta {consecutivo} creada desde cotización {cotizacion.numero}",
    )
    flash(f"Cuenta de cobro {consecutivo} generada.", "success")
    return redirect(url_for("cuentas_cobro.detalle", id=cuenta.id))
