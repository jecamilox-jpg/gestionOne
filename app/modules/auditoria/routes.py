"""
Visualización del registro de auditoría.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import RegistroAuditoria
from app.utils.decoradores import admin_requerido

bp = Blueprint("auditoria", __name__, template_folder="../../templates/auditoria")


@bp.route("/")
@login_required
@admin_requerido
def lista():
    busqueda = request.args.get("q", "").strip()
    accion = request.args.get("accion", "")
    modulo = request.args.get("modulo", "")
    pagina = int(request.args.get("pagina", 1))

    query = RegistroAuditoria.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            or_(
                RegistroAuditoria.usuario_nombre.ilike(like),
                RegistroAuditoria.descripcion.ilike(like),
                RegistroAuditoria.ip.ilike(like),
            )
        )
    if accion:
        query = query.filter_by(accion=accion)
    if modulo:
        query = query.filter_by(modulo=modulo)

    paginacion = query.order_by(RegistroAuditoria.fecha.desc()).paginate(
        page=pagina, per_page=25, error_out=False
    )
    return render_template(
        "auditoria/lista.html",
        paginacion=paginacion,
        busqueda=busqueda,
        accion=accion,
        modulo=modulo,
    )
