"""
CRUD de Presupuesto — gastos mensuales con distribución quincenal Q1/Q2.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models import ItemPresupuesto
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("presupuesto", __name__, template_folder="../../templates/presupuesto")


def _query_base():
    return ItemPresupuesto.query.filter_by(empresa_id=current_user.empresa_id)


@bp.route("/")
@login_required
def lista():
    # Mes actual por defecto
    hoy = datetime.today()
    mes = request.args.get("mes", hoy.strftime("%Y-%m"))
    tipo = request.args.get("tipo", "")

    query = _query_base().filter_by(mes=mes)
    if tipo:
        query = query.filter_by(tipo=tipo)

    items = query.order_by(ItemPresupuesto.concepto).all()

    # Totales
    total_costo = sum(i.costo for i in items)
    total_q1 = sum(i.valor_q1 for i in items)
    total_q2 = sum(i.valor_q2 for i in items)

    if request.headers.get("HX-Request"):
        return render_template(
            "presupuesto/_tabla.html",
            items=items, total_costo=total_costo,
            total_q1=total_q1, total_q2=total_q2,
        )

    return render_template(
        "presupuesto/lista.html",
        items=items, mes=mes, tipo=tipo,
        total_costo=total_costo, total_q1=total_q1, total_q2=total_q2,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nuevo():
    if request.method == "POST":
        item = ItemPresupuesto(
            concepto=request.form["concepto"].strip(),
            tipo=request.form.get("tipo", "personal"),
            costo=float(request.form.get("costo", 0)),
            fecha_pago=request.form.get("fecha_pago", "").strip(),
            destino=request.form.get("destino", "").strip(),
            porcentaje_q1=float(request.form.get("porcentaje_q1", 1)),
            porcentaje_q2=float(request.form.get("porcentaje_q2", 0)),
            mes=request.form.get("mes", datetime.today().strftime("%Y-%m")),
            empresa_id=current_user.empresa_id,
        )
        db.session.add(item)
        db.session.commit()
        registrar_evento("crear", "presupuesto", f"Item: {item.concepto}")
        flash("Gasto agregado al presupuesto.", "success")
        return redirect(url_for("presupuesto.lista", mes=item.mes))

    mes = request.args.get("mes", datetime.today().strftime("%Y-%m"))
    return render_template("presupuesto/form.html", item=None, mes=mes)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    item = _query_base().filter_by(id=id).first_or_404()
    if request.method == "POST":
        item.concepto = request.form["concepto"].strip()
        item.tipo = request.form.get("tipo", "personal")
        item.costo = float(request.form.get("costo", 0))
        item.fecha_pago = request.form.get("fecha_pago", "").strip()
        item.destino = request.form.get("destino", "").strip()
        item.porcentaje_q1 = float(request.form.get("porcentaje_q1", 1))
        item.porcentaje_q2 = float(request.form.get("porcentaje_q2", 0))
        item.mes = request.form.get("mes", item.mes)
        db.session.commit()
        registrar_evento("editar", "presupuesto", f"Item: {item.concepto}")
        flash("Gasto actualizado.", "success")
        return redirect(url_for("presupuesto.lista", mes=item.mes))

    return render_template("presupuesto/form.html", item=item, mes=item.mes)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    item = _query_base().filter_by(id=id).first_or_404()
    mes = item.mes
    nombre = item.concepto
    db.session.delete(item)
    db.session.commit()
    registrar_evento("eliminar", "presupuesto", f"Item eliminado: {nombre}")
    flash("Gasto eliminado del presupuesto.", "success")
    return redirect(url_for("presupuesto.lista", mes=mes))


@bp.route("/duplicar-mes", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def duplicar_mes():
    """Copia todos los items de un mes a otro."""
    mes_origen = request.form.get("mes_origen", "")
    mes_destino = request.form.get("mes_destino", "")
    if not mes_origen or not mes_destino or mes_origen == mes_destino:
        flash("Selecciona un mes origen y destino diferentes.", "warning")
        return redirect(url_for("presupuesto.lista"))

    items_origen = _query_base().filter_by(mes=mes_origen).all()
    if not items_origen:
        flash(f"No hay items en {mes_origen} para copiar.", "warning")
        return redirect(url_for("presupuesto.lista"))

    for orig in items_origen:
        nuevo = ItemPresupuesto(
            concepto=orig.concepto,
            tipo=orig.tipo,
            costo=orig.costo,
            fecha_pago=orig.fecha_pago,
            destino=orig.destino,
            porcentaje_q1=orig.porcentaje_q1,
            porcentaje_q2=orig.porcentaje_q2,
            mes=mes_destino,
            empresa_id=current_user.empresa_id,
        )
        db.session.add(nuevo)

    db.session.commit()
    registrar_evento("crear", "presupuesto", f"Duplicado {mes_origen} → {mes_destino} ({len(items_origen)} items)")
    flash(f"{len(items_origen)} gastos copiados a {mes_destino}.", "success")
    return redirect(url_for("presupuesto.lista", mes=mes_destino))
