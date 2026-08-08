"""
Módulo de Cuentas de Cobro.
"""
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, make_response,
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models import CuentaCobro, Cliente, PlantillaLayout, Cotizacion, ItemCuentaCobro, Producto
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento
from app.utils.pdf import generar_pdf_cuenta_cobro
from app.utils.correo import enviar_correo

bp = Blueprint("cuentas_cobro", __name__, template_folder="../../templates/cuentas_cobro")


def _query_base():
    return CuentaCobro.query.filter_by(empresa_id=current_user.empresa_id)


def _siguiente_consecutivo():
    ultima = (
        CuentaCobro.query.filter_by(empresa_id=current_user.empresa_id)
        .order_by(CuentaCobro.id.desc())
        .first()
    )
    siguiente = (ultima.id + 1) if ultima else 1
    return f"CC-{siguiente:06d}"


@bp.route("/")
@login_required
def lista():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    pagina = int(request.args.get("pagina", 1))

    query = _query_base().join(Cliente)
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            or_(CuentaCobro.consecutivo.ilike(like), Cliente.nombre.ilike(like))
        )
    if estado:
        query = query.filter(CuentaCobro.estado == estado)

    paginacion = query.order_by(CuentaCobro.creada_en.desc()).paginate(
        page=pagina, per_page=15, error_out=False
    )
    return render_template(
        "cuentas_cobro/lista.html",
        paginacion=paginacion, busqueda=busqueda, estado=estado,
    )


@bp.route("/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nueva():
    if request.method == "POST":
        cuenta = CuentaCobro(
            consecutivo=_siguiente_consecutivo(),
            fecha=datetime.strptime(request.form["fecha"], "%Y-%m-%d").date(),
            concepto=request.form.get("concepto", "").strip(),
            valor=0,
            estado=request.form.get("estado", "pendiente"),
            cliente_id=int(request.form["cliente_id"]),
            empresa_id=current_user.empresa_id,
            usuario_id=current_user.id,
        )
        db.session.add(cuenta)
        db.session.flush()

        descripciones = request.form.getlist("item_descripcion[]")
        cantidades = request.form.getlist("item_cantidad[]")
        valores = request.form.getlist("item_valor[]")
        total = 0
        for desc, cant, val in zip(descripciones, cantidades, valores):
            desc = desc.strip()
            if not desc:
                continue
            c = float(cant or 1)
            v = float(val or 0)
            db.session.add(ItemCuentaCobro(
                cuenta_id=cuenta.id, descripcion=desc,
                cantidad=c, valor_unitario=v,
            ))
            total += c * v

        cuenta.valor = total or float(request.form.get("valor") or 0)
        db.session.commit()
        registrar_evento("crear", "cuentas_cobro", f"Cuenta {cuenta.consecutivo}")
        flash("Cuenta de cobro creada.", "success")
        return redirect(url_for("cuentas_cobro.detalle", id=cuenta.id))

    clientes = Cliente.query.filter_by(
        empresa_id=current_user.empresa_id, estado="activo"
    ).order_by(Cliente.nombre).all()
    productos = Producto.query.filter_by(
        empresa_id=current_user.empresa_id, estado="activo"
    ).order_by(Producto.nombre).all()
    return render_template("cuentas_cobro/form.html", cuenta=None, clientes=clientes, productos=productos)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    cuenta = _query_base().filter_by(id=id).first_or_404()
    if cuenta.estado == "pagada":
        flash("No se pueden editar cuentas pagadas.", "warning")
        return redirect(url_for("cuentas_cobro.detalle", id=id))

    if request.method == "POST":
        cuenta.fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d").date()
        cuenta.concepto = request.form.get("concepto", "").strip()
        cuenta.estado = request.form.get("estado", "pendiente")
        cuenta.cliente_id = int(request.form["cliente_id"])

        for item in list(cuenta.items):
            db.session.delete(item)

        descripciones = request.form.getlist("item_descripcion[]")
        cantidades = request.form.getlist("item_cantidad[]")
        valores = request.form.getlist("item_valor[]")
        total = 0
        for desc, cant, val in zip(descripciones, cantidades, valores):
            desc = desc.strip()
            if not desc:
                continue
            c = float(cant or 1)
            v = float(val or 0)
            db.session.add(ItemCuentaCobro(
                cuenta_id=cuenta.id, descripcion=desc,
                cantidad=c, valor_unitario=v,
            ))
            total += c * v

        cuenta.valor = total or float(request.form.get("valor") or 0)
        db.session.commit()
        registrar_evento("editar", "cuentas_cobro", f"Cuenta {cuenta.consecutivo}")
        flash("Cuenta actualizada.", "success")
        return redirect(url_for("cuentas_cobro.detalle", id=id))

    clientes = Cliente.query.filter_by(
        empresa_id=current_user.empresa_id
    ).order_by(Cliente.nombre).all()
    productos = Producto.query.filter_by(
        empresa_id=current_user.empresa_id, estado="activo"
    ).order_by(Producto.nombre).all()
    return render_template("cuentas_cobro/form.html", cuenta=cuenta, clientes=clientes, productos=productos)


@bp.route("/<int:id>")
@login_required
def detalle(id):
    cuenta = _query_base().filter_by(id=id).first_or_404()
    plantillas = PlantillaLayout.query.filter_by(
        empresa_id=current_user.empresa_id, tipo="cuenta_cobro"
    ).all()
    return render_template(
        "cuentas_cobro/detalle.html", cuenta=cuenta, plantillas=plantillas
    )


@bp.route("/<int:id>/marcar/<estado>", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def marcar(id, estado):
    if estado not in ("pendiente", "pagada", "anulada"):
        flash("Estado inválido.", "danger")
        return redirect(url_for("cuentas_cobro.lista"))

    cuenta = _query_base().filter_by(id=id).first_or_404()
    cuenta.estado = estado
    if estado == "pagada":
        cuenta.fecha_pago = datetime.utcnow().date()
    db.session.commit()
    registrar_evento("editar", "cuentas_cobro", f"{cuenta.consecutivo} -> {estado}")
    flash(f"Cuenta marcada como {estado}.", "success")
    return redirect(url_for("cuentas_cobro.detalle", id=id))


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    cuenta = _query_base().filter_by(id=id).first_or_404()
    consecutivo = cuenta.consecutivo
    db.session.delete(cuenta)
    db.session.commit()
    registrar_evento("eliminar", "cuentas_cobro", f"Cuenta eliminada: {consecutivo}")
    flash("Cuenta eliminada.", "success")
    return redirect(url_for("cuentas_cobro.lista"))


@bp.route("/<int:id>/pdf")
@login_required
def pdf(id):
    cuenta = _query_base().filter_by(id=id).first_or_404()
    plantilla_id = request.args.get("plantilla_id", type=int)
    if plantilla_id:
        # El usuario pidió explícitamente una plantilla
        plantilla = PlantillaLayout.query.filter_by(
            id=plantilla_id, empresa_id=current_user.empresa_id
        ).first()
    else:
        # Sin plantilla_id en la URL: usar la predeterminada de la empresa
        plantilla = PlantillaLayout.query.filter_by(
            tipo="cuenta_cobro",
            empresa_id=current_user.empresa_id,
            es_predeterminada=True,
        ).first()
    contenido, ctype, ext = generar_pdf_cuenta_cobro(cuenta, plantilla=plantilla)
    response = make_response(contenido)
    response.headers["Content-Type"] = ctype
    response.headers["Content-Disposition"] = (
        f'inline; filename="{cuenta.consecutivo}.{ext}"'
    )
    registrar_evento("exportar_pdf", "cuentas_cobro", f"PDF {cuenta.consecutivo}")
    return response


@bp.route("/<int:id>/enviar", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def enviar(id):
    cuenta = _query_base().filter_by(id=id).first_or_404()
    destinatario = request.form.get("destinatario", "").strip() or (cuenta.cliente.correo or "")
    if not destinatario:
        flash("No se especificó un destinatario válido.", "danger")
        return redirect(url_for("cuentas_cobro.detalle", id=id))

    contenido, ctype, ext = generar_pdf_cuenta_cobro(cuenta)
    asunto = f"Cuenta de Cobro {cuenta.consecutivo} - {cuenta.empresa.nombre}"
    cuerpo = render_template("cuentas_cobro/correo.html", cuenta=cuenta)
    ok, mensaje = enviar_correo(
        destinatario, asunto, cuerpo,
        adjuntos=[(f"{cuenta.consecutivo}.{ext}", contenido, ctype)],
    )
    if ok:
        registrar_evento(
            "enviar_correo", "cuentas_cobro",
            f"Enviada {cuenta.consecutivo} a {destinatario}",
        )
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect(url_for("cuentas_cobro.detalle", id=id))
