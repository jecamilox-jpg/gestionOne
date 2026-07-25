"""
GestiónOne - Punto de entrada de la aplicación
==============================================
Ejecutar con:
    python app.py

Crea la app Flask, inicializa la base de datos (si no existe),
crea un usuario administrador por defecto y arranca el servidor
de desarrollo.
"""
import os
from app import create_app, db
from app.models import (
    Usuario, Empresa, Cliente, Producto,
    Cotizacion, CuentaCobro, PlantillaLayout
)
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
    Crea las tablas (si no existen) e inserta los datos iniciales:
    una empresa demo y un usuario administrador.
    """
    with app.app_context():
        db.create_all()

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
        if not Usuario.query.filter_by(username="admin").first():
            empresa = Empresa.query.first()
            admin = Usuario(
                username="admin",
                nombre_completo="Administrador",
                correo="admin@gestionone.com",
                rol="administrador",
                activo=True,
                empresa_id=empresa.id,
            )
            admin.password_hash = generate_password_hash("admin123")
            db.session.add(admin)
            db.session.commit()
            print("  -> Usuario admin creado (usuario: admin / clave: admin123)")


if __name__ == "__main__":
    print("=" * 60)
    print("  GestiónOne - Iniciando aplicación")
    print("=" * 60)
    inicializar_base_datos()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"  Servidor: http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=debug)
