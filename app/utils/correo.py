"""
Envío de correos vía SMTP estándar de Python (sin Flask-Mail).
"""
import smtplib
from email.message import EmailMessage
from flask import current_app


def enviar_correo(destinatarios, asunto, cuerpo_html, adjuntos=None):
    """
    Envía un correo HTML opcionalmente con adjuntos.

    Args:
        destinatarios: lista de correos o un string
        asunto: asunto del correo
        cuerpo_html: contenido en HTML
        adjuntos: lista de tuplas (nombre_archivo, bytes, content_type)

    Returns:
        (ok: bool, mensaje: str)
    """
    cfg = current_app.config
    if not cfg.get("MAIL_USERNAME") or not cfg.get("MAIL_PASSWORD"):
        return False, "SMTP no configurado. Define MAIL_USERNAME y MAIL_PASSWORD."

    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False, "No hay destinatarios."

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = cfg.get("MAIL_DEFAULT_SENDER") or cfg["MAIL_USERNAME"]
    msg["To"] = ", ".join(destinatarios)
    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(cuerpo_html, subtype="html")

    if adjuntos:
        for nombre, contenido, ctype in adjuntos:
            maintype, _, subtype = ctype.partition("/")
            msg.add_attachment(
                contenido, maintype=maintype, subtype=subtype, filename=nombre
            )

    try:
        if cfg.get("MAIL_USE_TLS"):
            with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=15) as smtp:
                smtp.starttls()
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=15) as smtp:
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
                smtp.send_message(msg)
        return True, "Correo enviado correctamente."
    except Exception as exc:
        return False, f"Error al enviar: {exc}"
