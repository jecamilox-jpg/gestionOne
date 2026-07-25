"""
Módulo de autenticación: login, logout y recuperación de contraseña.
"""
import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import Usuario
from app.utils.auditoria import registrar_evento

bp = Blueprint("auth", __name__, template_folder="../../templates/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        recordar = bool(request.form.get("recordar"))

        usuario = Usuario.query.filter(
            (Usuario.username == username) | (Usuario.correo == username)
        ).first()

        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash("Tu cuenta está desactivada. Contacta al administrador.", "warning")
                return render_template("auth/login.html")

            login_user(usuario, remember=recordar)
            usuario.ultimo_login = datetime.utcnow()
            db.session.commit()
            registrar_evento("login", "auth", f"Inicio de sesión de {usuario.username}")

            siguiente = request.args.get("next")
            return redirect(siguiente or url_for("dashboard.index"))

        flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    """Cierre de sesión."""
    registrar_evento("logout", "auth", f"Cierre de sesión de {current_user.username}")
    logout_user()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/recuperar", methods=["GET", "POST"])
def recuperar_password():
    """
    Estructura preparada para recuperación de contraseña.
    Genera un token y (en un entorno real) lo enviaría por correo.
    """
    if request.method == "POST":
        correo = request.form.get("correo", "").strip()
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario:
            usuario.token_reset = secrets.token_urlsafe(32)
            db.session.commit()
            # En producción aquí se enviaría el correo con el token
            flash(
                "Si el correo existe en el sistema, recibirás instrucciones para "
                "restablecer tu contraseña.",
                "info",
            )
        else:
            flash(
                "Si el correo existe en el sistema, recibirás instrucciones para "
                "restablecer tu contraseña.",
                "info",
            )
        return redirect(url_for("auth.login"))

    return render_template("auth/recuperar.html")


@bp.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer_password(token):
    """Permite restablecer la clave usando un token válido."""
    usuario = Usuario.query.filter_by(token_reset=token).first()
    if not usuario:
        flash("Enlace inválido o expirado.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nueva = request.form.get("password", "")
        confirmacion = request.form.get("password2", "")
        if nueva != confirmacion or len(nueva) < 6:
            flash("Las contraseñas no coinciden o son demasiado cortas.", "danger")
        else:
            usuario.set_password(nueva)
            usuario.token_reset = None
            db.session.commit()
            flash("Contraseña actualizada. Inicia sesión.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/restablecer.html", token=token)
