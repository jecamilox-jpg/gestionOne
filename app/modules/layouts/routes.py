"""
Diseñador de plantillas (Layout Designer) basado en GrapesJS.

Permite crear, editar y guardar plantillas para cotizaciones y cuentas de
cobro con elementos arrastrables (logo, texto, tabla, firma, imagen y QR).
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
)
from flask_login import login_required, current_user

from app import db
from app.models import PlantillaLayout
from app.utils.decoradores import rol_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("layouts", __name__, template_folder="../../templates/layouts")


def _query_base():
    return PlantillaLayout.query.filter_by(empresa_id=current_user.empresa_id)


@bp.route("/")
@login_required
def lista():
    plantillas = _query_base().order_by(PlantillaLayout.actualizada_en.desc()).all()
    return render_template("layouts/lista.html", plantillas=plantillas)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def nuevo():
    if request.method == "POST":
        plantilla = PlantillaLayout(
            nombre=request.form["nombre"].strip(),
            tipo=request.form.get("tipo", "cotizacion"),
            empresa_id=current_user.empresa_id,
        )
        db.session.add(plantilla)
        db.session.commit()
        registrar_evento("crear", "layouts", f"Plantilla {plantilla.nombre}")
        return redirect(url_for("layouts.editor", id=plantilla.id))

    return render_template("layouts/nuevo.html")


@bp.route("/<int:id>")
@login_required
def editor(id):
    plantilla = _query_base().filter_by(id=id).first_or_404()
    return render_template("layouts/editor.html", plantilla=plantilla)


@bp.route("/<int:id>/guardar", methods=["POST"])
@login_required
@rol_requerido("administrador", "vendedor")
def guardar(id):
    """Endpoint AJAX llamado por GrapesJS para persistir cambios."""
    plantilla = _query_base().filter_by(id=id).first_or_404()
    data = request.get_json(silent=True) or {}
    plantilla.html_contenido = data.get("html", "")
    plantilla.css_contenido = data.get("css", "")
    plantilla.componentes_json = data.get("components", "")
    plantilla.estilos_json = data.get("styles", "")
    db.session.commit()
    registrar_evento("editar", "layouts", f"Plantilla {plantilla.nombre} guardada")
    return jsonify({"ok": True, "mensaje": "Plantilla guardada"})


@bp.route("/<int:id>/predeterminada", methods=["POST"])
@login_required
@rol_requerido("administrador")
def hacer_predeterminada(id):
    plantilla = _query_base().filter_by(id=id).first_or_404()
    # Quitar predeterminada anterior del mismo tipo
    _query_base().filter_by(tipo=plantilla.tipo).update({"es_predeterminada": False})
    plantilla.es_predeterminada = True
    db.session.commit()
    registrar_evento(
        "editar", "layouts", f"Plantilla {plantilla.nombre} como predeterminada"
    )
    flash("Plantilla establecida como predeterminada.", "success")
    return redirect(url_for("layouts.lista"))


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("administrador")
def eliminar(id):
    plantilla = _query_base().filter_by(id=id).first_or_404()
    nombre = plantilla.nombre
    db.session.delete(plantilla)
    db.session.commit()
    registrar_evento("eliminar", "layouts", f"Plantilla eliminada: {nombre}")
    flash("Plantilla eliminada.", "success")
    return redirect(url_for("layouts.lista"))
