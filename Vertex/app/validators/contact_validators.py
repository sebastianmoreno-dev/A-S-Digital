"""Validaciones anti-bot del formulario de contacto: honeypot y tiempo mínimo.

Estas dos reglas son intencionalmente silenciosas de cara al usuario: un
bot que las dispara recibe la misma respuesta de "éxito" que un envío
real, para no darle pistas de que fue detectado. El evento sí queda
registrado en la bitácora.
"""
import time

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_SALT = 'contact-form-timestamp'
_MAX_AGE_SECONDS = 1800  # 30 min: un formulario más viejo que esto se considera stale


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def make_form_timestamp() -> str:
    """Token firmado que se embebe como campo oculto al renderizar el form."""
    return _serializer().dumps({'t': time.time()})


def seconds_since_render(token: str) -> float | None:
    """Segundos transcurridos desde que se generó el token.

    Devuelve None si el token falta, fue manipulado o expiró — en
    cualquiera de esos casos el llamador debe tratarlo como sospechoso.
    """
    if not token:
        return None
    try:
        data = _serializer().loads(token, max_age=_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return time.time() - data.get('t', 0)


def is_honeypot_filled(value: str | None) -> bool:
    return bool(value and value.strip())


def is_submission_too_fast(token: str, min_seconds: int) -> bool:
    """True si el form se envió antes del tiempo mínimo humano razonable."""
    elapsed = seconds_since_render(token)
    if elapsed is None:
        return True  # token ausente/inválido/expirado -> tratar como bot
    return elapsed < min_seconds
