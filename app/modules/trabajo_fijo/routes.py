"""
CRUD de Trabajo Fijo — empleo formal con cálculo de liquidación laboral colombiana.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models import TrabajoFijo
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("trabajo_fijo", __name__, template_folder="../../templates/trabajo_fijo")


def _query_base():
    return TrabajoFijo.query.filter_by(empresa_id=current_user.empresa_id)


@bp.route("/")
@login_required
def lista():
    estado = request.args.get("estado", "")
    query = _query_base()
    if estado:
        query = query.filter_by(estado=estado)

    trabajos = query.order_by(TrabajoFijo.fecha_ingreso.desc()).all()

    if request.headers.get("HX-Request"):
        return render_template("trabajo_fijo/_tabla.html", trabajos=trabajos)

    return render_template("trabajo_fijo/lista.html", trabajos=trabajos, estado=estado)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nuevo():
    if request.method == "POST":
        trabajo = TrabajoFijo(
            empresa_nombre=request.form["empresa_nombre"].strip(),
            fecha_ingreso=datetime.strptime(request.form["fecha_ingreso"], "%Y-%m-%d").date(),
            salario_base=float(request.form.get("salario_base", 0)),
            auxilio_transporte=float(request.form.get("auxilio_transporte", 0)),
            estado=request.form.get("estado", "activo"),
            notas=request.form.get("notas", "").strip(),
            empresa_id=current_user.empresa_id,
        )
        db.session.add(trabajo)
        db.session.commit()
        registrar_evento("crear", "trabajo_fijo", f"Trabajo: {trabajo.empresa_nombre}")
        flash("Trabajo fijo registrado correctamente.", "success")
        return redirect(url_for("trabajo_fijo.lista"))

    return render_template("trabajo_fijo/form.html", trabajo=None)


@bp.route("/<int:id>")
@login_required
def detalle(id):
    trabajo = _query_base().filter_by(id=id).first_or_404()
    return render_template("trabajo_fijo/detalle.html", trabajo=trabajo)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def editar(id):
    trabajo = _query_base().filter_by(id=id).first_or_404()
    if request.method == "POST":
        trabajo.empresa_nombre = request.form["empresa_nombre"].strip()
        trabajo.fecha_ingreso = datetime.strptime(request.form["fecha_ingreso"], "%Y-%m-%d").date()
        trabajo.salario_base = float(request.form.get("salario_base", 0))
        trabajo.auxilio_transporte = float(request.form.get("auxilio_transporte", 0))
        trabajo.estado = request.form.get("estado", "activo")
        trabajo.notas = request.form.get("notas", "").strip()
        db.session.commit()
        registrar_evento("editar", "trabajo_fijo", f"Trabajo: {trabajo.empresa_nombre}")
        flash("Trabajo fijo actualizado.", "success")
        return redirect(url_for("trabajo_fijo.detalle", id=trabajo.id))

    return render_template("trabajo_fijo/form.html", trabajo=trabajo)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    trabajo = _query_base().filter_by(id=id).first_or_404()
    nombre = trabajo.empresa_nombre
    db.session.delete(trabajo)
    db.session.commit()
    registrar_evento("eliminar", "trabajo_fijo", f"Trabajo eliminado: {nombre}")
    flash("Trabajo fijo eliminado.", "success")
    return redirect(url_for("trabajo_fijo.lista"))
