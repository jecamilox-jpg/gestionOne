"""
Gestión multiempresa.
"""
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, send_from_directory,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Empresa
from app.utils.decoradores import admin_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("empresas", __name__, template_folder="../../templates/empresas")

EXTS_LOGO = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def _extension_valida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTS_LOGO


@bp.route("/")
@login_required
@admin_requerido
def lista():
    empresas = Empresa.query.order_by(Empresa.nombre).all()
    return render_template("empresas/lista.html", empresas=empresas)


@bp.route("/nueva", methods=["GET", "POST"])
@login_required
@admin_requerido
def nueva():
    if request.method == "POST":
        empresa = Empresa(
            nombre=request.form["nombre"].strip(),
            nit=request.form["nit"].strip(),
            direccion=request.form.get("direccion", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            correo=request.form.get("correo", "").strip(),
            pago_llave=request.form.get("pago_llave", "").strip() or None,
            pago_daviplata=request.form.get("pago_daviplata", "").strip() or None,
            pago_nequi=request.form.get("pago_nequi", "").strip() or None,
            pago_extra_label=request.form.get("pago_extra_label", "").strip() or None,
            pago_extra_valor=request.form.get("pago_extra_valor", "").strip() or None,
            tipografia=request.form.get("tipografia", "century_gothic").strip(),
        )
        logo = request.files.get("logo")
        if logo and logo.filename and _extension_valida(logo.filename):
            nombre = secure_filename(f"logo_{empresa.nit}_{logo.filename}")
            ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre)
            logo.save(ruta)
            empresa.logo = nombre

        firma = request.files.get("firma")
        if firma and firma.filename and _extension_valida(firma.filename):
            nombre = secure_filename(f"firma_{empresa.nit}_{firma.filename}")
            ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre)
            firma.save(ruta)
            empresa.firma = nombre

        db.session.add(empresa)
        db.session.commit()
        registrar_evento("crear", "empresas", f"Empresa creada: {empresa.nombre}")
        flash("Empresa creada correctamente.", "success")
        return redirect(url_for("empresas.lista"))

    return render_template("empresas/form.html", empresa=None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@admin_requerido
def editar(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == "POST":
        empresa.nombre = request.form["nombre"].strip()
        empresa.nit = request.form["nit"].strip()
        empresa.direccion = request.form.get("direccion", "").strip()
        empresa.telefono = request.form.get("telefono", "").strip()
        empresa.correo = request.form.get("correo", "").strip()
        empresa.pago_llave = request.form.get("pago_llave", "").strip() or None
        empresa.pago_daviplata = request.form.get("pago_daviplata", "").strip() or None
        empresa.pago_nequi = request.form.get("pago_nequi", "").strip() or None
        empresa.pago_extra_label = request.form.get("pago_extra_label", "").strip() or None
        empresa.pago_extra_valor = request.form.get("pago_extra_valor", "").strip() or None
        empresa.tipografia = request.form.get("tipografia", "century_gothic").strip()

        logo = request.files.get("logo")
        if logo and logo.filename and _extension_valida(logo.filename):
            nombre = secure_filename(f"logo_{empresa.nit}_{logo.filename}")
            ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre)
            logo.save(ruta)
            empresa.logo = nombre

        firma = request.files.get("firma")
        if firma and firma.filename and _extension_valida(firma.filename):
            nombre = secure_filename(f"firma_{empresa.nit}_{firma.filename}")
            ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre)
            firma.save(ruta)
            empresa.firma = nombre

        db.session.commit()
        registrar_evento("editar", "empresas", f"Empresa editada: {empresa.nombre}")
        flash("Empresa actualizada.", "success")
        return redirect(url_for("empresas.lista"))

    return render_template("empresas/form.html", empresa=empresa)


@bp.route("/logo/<filename>")
@login_required
def logo(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@bp.route("/firma/<filename>")
@login_required
def firma_archivo(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
