"""
Factoría de la aplicación Flask.

Inicializa todas las extensiones (SQLAlchemy, Login, Migrate) y
registra los blueprints de cada módulo del sistema.
"""
import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

from config import get_config

# --- Extensiones (instancias únicas, sin app aún) ---
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=None):
    """Crea y configura la instancia de Flask."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Configuración
    app.config.from_object(config_class or get_config())

    # Crear carpetas de uploads/exports si no existen
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXPORT_FOLDER"], exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para continuar."
    login_manager.login_message_category = "warning"

    # Cargar modelos (necesario para que SQLAlchemy los registre)
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return models.Usuario.query.get(int(user_id))

    # --- Registro de blueprints ---
    from app.modules.auth.routes import bp as auth_bp
    from app.modules.dashboard.routes import bp as dashboard_bp
    from app.modules.empresas.routes import bp as empresas_bp
    from app.modules.clientes.routes import bp as clientes_bp
    from app.modules.productos.routes import bp as productos_bp
    from app.modules.cotizaciones.routes import bp as cotizaciones_bp
    from app.modules.cuentas_cobro.routes import bp as cuentas_bp
    from app.modules.layouts.routes import bp as layouts_bp
    from app.modules.auditoria.routes import bp as auditoria_bp
    from app.modules.usuarios.routes import bp as usuarios_bp
    from app.modules.infraestructura import infra_bp
    from app.modules.trabajo_fijo.routes import bp as trabajo_fijo_bp
    from app.modules.presupuesto.routes import bp as presupuesto_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(trabajo_fijo_bp, url_prefix="/trabajo-fijo")
    app.register_blueprint(presupuesto_bp, url_prefix="/presupuesto")
    app.register_blueprint(empresas_bp, url_prefix="/empresas")
    app.register_blueprint(clientes_bp, url_prefix="/clientes")
    app.register_blueprint(productos_bp, url_prefix="/productos")
    app.register_blueprint(cotizaciones_bp, url_prefix="/cotizaciones")
    app.register_blueprint(cuentas_bp, url_prefix="/cuentas-cobro")
    app.register_blueprint(layouts_bp, url_prefix="/layouts")
    app.register_blueprint(auditoria_bp, url_prefix="/auditoria")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(infra_bp)  # rutas tipo /clientes/<id>/infraestructura/...

    # Ruta raíz: redirige al dashboard o login
    @app.route("/inicio")
    def inicio():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # Filtros Jinja personalizados
    from app.utils import filtros
    filtros.registrar(app)

    # Context processor: empresa activa y modelos disponibles en todas las plantillas
    @app.context_processor
    def inject_globales():
        from app.utils.tipografias import obtener_tipografia, stack_css, TIPOGRAFIA_DEFAULT

        if current_user.is_authenticated and current_user.empresa:
            empresa_activa = current_user.empresa
        else:
            empresa_activa = models.Empresa.query.first()

        # Determinar la tipografía activa
        id_tipografia = (empresa_activa.tipografia
                         if empresa_activa and empresa_activa.tipografia
                         else TIPOGRAFIA_DEFAULT)
        tipografia = obtener_tipografia(id_tipografia)

        return {
            "empresa_activa": empresa_activa,
            "tipografia_activa": tipografia,
            "tipografia_stack": stack_css(id_tipografia),
            # Modelos para uso en plantillas (ordenar relaciones dinámicas)
            "Cliente": models.Cliente,
            "Producto": models.Producto,
            "Cotizacion": models.Cotizacion,
            "CuentaCobro": models.CuentaCobro,
            "Usuario": models.Usuario,
            "Empresa": models.Empresa,
        }

    return app
