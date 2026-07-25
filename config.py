"""
Configuración central de GestiónOne.

Soporta dos entornos:
  - desarrollo  -> SQLite local
  - produccion  -> PostgreSQL (a partir de DATABASE_URL, p. ej. en Railway)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class BaseConfig:
    """Configuración base común a todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion-gestionone")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Subidas. En Railway debe apuntar al Volume montado (ej. /data/uploads)
    # para que los archivos persistan entre redeploys. Si no se define la var
    # de entorno, usa la carpeta uploads/ local del proyecto.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or str(BASE_DIR / "uploads")
    EXPORT_FOLDER = os.environ.get("EXPORT_FOLDER") or str(BASE_DIR / "exports")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    # SMTP (configurable por variables de entorno)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "no-reply@gestionone.com"
    )

    # Paginación
    ITEMS_POR_PAGINA = 15


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'gestionone.db'}"
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Railway expone DATABASE_URL en formato postgres://, lo normalizamos
    _db_url = os.environ.get("DATABASE_URL", "")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{BASE_DIR / 'gestionone.db'}"


# Diccionario de selección de entorno
config_by_name = {
    "desarrollo": DevelopmentConfig,
    "produccion": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Devuelve la clase de configuración según FLASK_ENV."""
    env = os.environ.get("FLASK_ENV", "desarrollo")
    return config_by_name.get(env, DevelopmentConfig)
