"""Hashing de contraseñas (argon2id) y generación/hash de tokens opacos."""
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _ph.check_needs_rehash(password_hash)
    except InvalidHash:
        return True


def generate_secure_token(nbytes: int = 32) -> str:
    """Token opaco para sesiones/recuperación de contraseña/verificación."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Solo se guarda el hash en BD; el token en claro nunca se persiste."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
