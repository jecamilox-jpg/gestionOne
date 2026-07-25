"""
Decoradores de control de acceso por rol.
"""
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def rol_requerido(*roles):
    """
    Restringe el acceso a una vista a usuarios cuyo rol esté en `roles`.

    Uso:
        @rol_requerido("administrador", "vendedor")
        def crear_cliente(): ...
    """
    def decorador(view):
        @wraps(view)
        def envoltorio(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.rol not in roles:
                flash("No tienes permisos para acceder a esta sección.", "danger")
                return redirect(url_for("dashboard.index"))
            return view(*args, **kwargs)
        return envoltorio
    return decorador


def admin_requerido(view):
    """Atajo: solo administradores."""
    return rol_requerido("administrador")(view)
