"""
GestiónOne - Punto de entrada de la aplicación
==============================================
Ejecutar con:
    python wsgi.py            (modo desarrollo local)
    gunicorn wsgi:app         (modo producción, usado por Railway)

Al arrancar:
  1. Crea las tablas en BD (si no existen)
  2. Crea una empresa y un usuario admin si la BD está vacía
  3. Instala la plantilla "Cuenta de cobro — Estilo Verde" como predeterminada
"""
import os
import secrets
from app import create_app, db
from app.models import (
    Usuario, Empresa, Cliente, Producto,
    Cotizacion, CuentaCobro, PlantillaLayout
)
from app.utils.plantilla_verde import instalar_plantilla_verde
from app.utils.plantilla_azul import instalar_plantilla_azul
from werkzeug.security import generate_password_hash


# Crear la instancia de la aplicación Flask
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Expone modelos al shell de Flask: `flask shell`."""
    return {
        "db": db,
        "Usuario": Usuario,
        "Empresa": Empresa,
        "Cliente": Cliente,
        "Producto": Producto,
        "Cotizacion": Cotizacion,
        "CuentaCobro": CuentaCobro,
        "PlantillaLayout": PlantillaLayout,
    }


def inicializar_base_datos():
    """
    Crea las tablas (si no existen) e inserta los datos iniciales.
    Se ejecuta tanto con `python wsgi.py` (dev) como con gunicorn (prod en Railway).

    Idempotente: si ya hay empresa/admin/plantilla, no duplica nada.
    """
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"  ⚠ Error creando tablas: {e}")
            return

        # === Mini-migración inline ===
        # db.create_all() NO altera tablas existentes. Cuando agregamos columnas
        # nuevas al modelo, hay que añadirlas manualmente con ALTER TABLE.
        # Aquí intentamos agregar las columnas nuevas; si ya existen, ignoramos el error.
        from sqlalchemy import text, inspect

        migraciones = [
            # (tabla, columna, sentencia ALTER)
            ("empresas", "firma",
             "ALTER TABLE empresas ADD COLUMN firma VARCHAR(255)"),
        ]
        inspector = inspect(db.engine)
        for tabla, columna, ddl in migraciones:
            try:
                if not inspector.has_table(tabla):
                    continue  # la tabla aún no existe, la creará db.create_all()
                cols = {c["name"] for c in inspector.get_columns(tabla)}
                if columna not in cols:
                    with db.engine.begin() as conn:
                        conn.execute(text(ddl))
                    print(f"  -> Migración aplicada: {tabla}.{columna}")
            except Exception as e:
                print(f"  ⚠ Migración {tabla}.{columna} falló: {e}")

        # Empresa demo si no existe ninguna
        if not Empresa.query.first():
            empresa = Empresa(
                nombre="Mi Empresa S.A.S",
                nit="900.123.456-7",
                direccion="Calle 100 # 10-20",
                telefono="+57 300 000 0000",
                correo="contacto@miempresa.com",
                logo=None,
            )
            db.session.add(empresa)
            db.session.commit()
            print(f"  -> Empresa demo creada: {empresa.nombre}")

        # Usuario admin por defecto
        # ATENCIÓN: en producción, define la variable de entorno ADMIN_PASSWORD
        # para que la contraseña inicial sea segura. Si no se define, se genera
        # una aleatoria y se muestra una sola vez en los logs.
        if not Usuario.query.filter_by(username="admin").first():
            empresa = Empresa.query.first()
            password_inicial = os.environ.get("ADMIN_PASSWORD")
            password_fue_generada = False
            if not password_inicial:
                # Genera una contraseña segura aleatoria si no se proveyó
                password_inicial = secrets.token_urlsafe(12)
                password_fue_generada = True

            admin = Usuario(
                username="admin",
                nombre_completo="Administrador",
                correo="admin@gestionone.com",
                rol="administrador",
                activo=True,
                empresa_id=empresa.id,
            )
            admin.password_hash = generate_password_hash(password_inicial)
            db.session.add(admin)
            db.session.commit()
            print("  -> Usuario admin creado")
            if password_fue_generada:
                print("  -> ⚠ CONTRASEÑA INICIAL GENERADA (cópiala AHORA, no se vuelve a mostrar):")
                print(f"      usuario: admin")
                print(f"      clave  : {password_inicial}")
                print("      Cambia esta contraseña inmediatamente desde el menú Usuarios.")
            else:
                print("  -> Contraseña inicial tomada de la variable ADMIN_PASSWORD")

        # Instalar/actualizar la plantilla 'Cuenta de cobro — Estilo Verde'
        # como predeterminada. Es idempotente: si ya existe la actualiza.
        try:
            plantilla = instalar_plantilla_verde()
            if plantilla:
                print(f"  -> Plantilla 'Estilo Verde' lista (id={plantilla.id})")
        except Exception as e:
            print(f"  ⚠ No se pudo instalar la plantilla verde: {e}")

        # Instalar/actualizar la plantilla 'Cuenta de cobro — Estilo Azul'.
        # NO la marca como predeterminada — el usuario elige cuál usar.
        try:
            plantilla_az = instalar_plantilla_azul()
            if plantilla_az:
                print(f"  -> Plantilla 'Estilo Azul' lista (id={plantilla_az.id})")
        except Exception as e:
            print(f"  ⚠ No se pudo instalar la plantilla azul: {e}")


# Ejecutar inicialización al cargar el módulo (funciona con gunicorn y con `python wsgi.py`)
# Se omite si FLASK_SKIP_INIT=1 está definida (útil para tests).
if os.environ.get("FLASK_SKIP_INIT", "0") != "1":
    inicializar_base_datos()


if __name__ == "__main__":
    print("=" * 60)
    print("  GestiónOne - Iniciando aplicación")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"  Servidor: http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=debug)
