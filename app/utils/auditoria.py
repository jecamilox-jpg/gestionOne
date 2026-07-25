"""
Helper para registrar eventos de auditoría.
"""
from flask import request
from flask_login import current_user
from app import db
from app.models import RegistroAuditoria


def registrar_evento(accion, modulo, descripcion=""):
    """
    Crea un registro de auditoría.

    Args:
        accion: crear | editar | eliminar | exportar_pdf | enviar_correo | login | logout
        modulo: nombre del módulo afectado
        descripcion: detalles libres
    """
    try:
        usuario_id = current_user.id if current_user.is_authenticated else None
        usuario_nombre = (
            current_user.nombre_completo if current_user.is_authenticated else "Anónimo"
        )
        ip = request.remote_addr if request else None

        registro = RegistroAuditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip=ip,
        )
        db.session.add(registro)
        db.session.commit()
    except Exception as exc:
        # Nunca debe romper el flujo principal
        db.session.rollback()
        print(f"[AUDITORIA] Error registrando evento: {exc}")
