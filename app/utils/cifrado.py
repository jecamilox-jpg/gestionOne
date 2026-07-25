"""
Cifrado simétrico de credenciales sensibles.

Usa Fernet (AES-128 en modo CBC + HMAC-SHA256) de la librería 'cryptography'.

La clave se obtiene de la variable de entorno ENCRYPTION_KEY. Si no existe,
la app NO permite usar el módulo de credenciales y muestra un error claro.

Para generar una clave nueva (UNA vez en la vida del proyecto):

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

⚠ Si pierdes la clave, las credenciales cifradas quedan irrecuperables.
⚠ Nunca commitees la clave al repositorio.
"""
import os
from cryptography.fernet import Fernet, InvalidToken


class CifradoNoConfigurado(Exception):
    """Se lanza cuando intentas usar el módulo de cifrado sin ENCRYPTION_KEY definida."""
    pass


def _get_fernet():
    """Obtiene la instancia de Fernet. Lanza CifradoNoConfigurado si no hay clave."""
    key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if not key:
        raise CifradoNoConfigurado(
            "Falta la variable de entorno ENCRYPTION_KEY. "
            "Genera una con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as e:
        raise CifradoNoConfigurado(
            f"ENCRYPTION_KEY no es válida: {e}. "
            "Debe ser un string base64 de 32 bytes generado con Fernet.generate_key()."
        )


def cifrar(texto_plano):
    """Cifra un string y devuelve el token cifrado como string."""
    if not texto_plano:
        return ""
    f = _get_fernet()
    return f.encrypt(texto_plano.encode("utf-8")).decode("ascii")


def descifrar(token_cifrado):
    """Descifra un token. Devuelve string vacío si el token es inválido."""
    if not token_cifrado:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(token_cifrado.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def esta_configurado():
    """Devuelve True si ENCRYPTION_KEY está definida y es válida."""
    try:
        _get_fernet()
        return True
    except CifradoNoConfigurado:
        return False
