"""
Script de utilidad para crear/actualizar manualmente la plantilla
'Cuenta de cobro — Estilo Verde'.

En producción NO es necesario ejecutar este script: la plantilla se
instala automáticamente al arrancar la app (ver wsgi.py).

Uso manual (por ejemplo si reseteaste la plantilla y quieres restaurarla):
    python crear_plantilla_verde.py
"""
import os
import sys

# Permitir ejecutar este script desde la raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.plantilla_verde import instalar_plantilla_verde

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        plantilla = instalar_plantilla_verde()
        if plantilla is None:
            print("⚠ No hay empresas en la BD. Arranca la app primero para que se cree la empresa demo.")
            sys.exit(1)
        print(f"✓ Plantilla '{plantilla.nombre}' instalada (id={plantilla.id})")
        print(f"  Empresa: {plantilla.empresa_id}")
        print(f"  Es predeterminada: {plantilla.es_predeterminada}")
