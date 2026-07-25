"""
Gestión de usuarios y roles.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Usuario, Empresa
from app.utils.decoradores import admin_requerido
from app.utils.auditoria import registrar_evento

bp = Blueprint("usuarios", __name__, template_folder="../../templates/usuarios")

ROLES_VALIDOS = ("administrador", "vendedor", "consulta")


@bp.route("/")
@login_required
@admin_requerido
def lista():
    usuarios = Usuario.query.order_by(Usuario.nombre_completo).all()
    return render_template("usuarios/lista.html", usuarios=usuarios)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_requerido
def nuevo():
    empresas = Empresa.query.order_by(Empresa.nombre).all()
    if request.method == "POST":
        username = request.form["username"].strip()
        if Usuario.query.filter_by(username=username).first():
            flash("Ya existe un usuario con ese nombre.", "danger")
            return render_template("usuarios/form.html", usuario=None, empresas=empresas)

        rol = request.form.get("rol", "vendedor")
        if rol not in ROLES_VALIDOS:
            rol = "vendedor"

        usuario = Usuario(
            username=username,
            nombre_completo=request.form["nombre_completo"].strip(),
            correo=request.form["correo"].strip(),
            rol=rol,
            activo=bool(request.form.get("activo")),
            empresa_id=int(request.form["empresa_id"]),
        )
        usuario.set_password(request.form.get("password") or "cambiar123")
        db.session.add(usuario)
        db.session.commit()
        registrar_evento("crear", "usuarios", f"Usuario creado: {username}")
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/form.html", usuario=None, empresas=empresas)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@admin_requerido
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    empresas = Empresa.query.order_by(Empresa.nombre).all()

    if request.method == "POST":
        usuario.nombre_completo = request.form["nombre_completo"].strip()
        usuario.correo = request.form["correo"].strip()
        rol = request.form.get("rol", "vendedor")
        if rol in ROLES_VALIDOS:
            usuario.rol = rol
        usuario.activo = bool(request.form.get("activo"))
        usuario.empresa_id = int(request.form["empresa_id"])

        nueva_password = request.form.get("password", "").strip()
        if nueva_password:
            usuario.set_password(nueva_password)

        db.session.commit()
        registrar_evento("editar", "usuarios", f"Usuario editado: {usuario.username}")
        flash("Usuario actualizado.", "success")
        return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/form.html", usuario=usuario, empresas=empresas)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@admin_requerido
def eliminar(id):
    if id == current_user.id:
        flash("No puedes eliminar tu propio usuario.", "danger")
        return redirect(url_for("usuarios.lista"))
    usuario = Usuario.query.get_or_404(id)
    username = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    registrar_evento("eliminar", "usuarios", f"Usuario eliminado: {username}")
    flash("Usuario eliminado.", "success")
    return redirect(url_for("usuarios.lista"))
