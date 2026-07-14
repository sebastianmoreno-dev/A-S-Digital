"""Headers de seguridad (CSP, HSTS, X-Frame-Options, etc.) vía Flask-Talisman.

Diseñado para no chocar con Cloudflare: no forzamos el redirect
HTTP->HTTPS aquí (Cloudflare ya lo hace con "Always Use HTTPS"),
evitando un posible loop de redirects en modo Flexible.
"""
from flask import Response

from app.extensions import talisman

# Solo se usan Google Fonts como recurso externo (ver base.html) — nada de CDNs.
CONTENT_SECURITY_POLICY = {
    'default-src': "'self'",
    'script-src': "'self'",
    'style-src': ["'self'", 'https://fonts.googleapis.com', "'unsafe-inline'"],
    'font-src': ['https://fonts.gstatic.com'],
    'img-src': ["'self'", 'data:'],
    'connect-src': "'self'",
    'object-src': "'none'",
    'base-uri': "'self'",
    'form-action': "'self'",
    'frame-ancestors': "'none'",
}

# style-src necesita 'unsafe-inline' porque las plantillas actuales usan
# style="" inline extensivamente. Eliminarlo requeriría refactorizar CSS
# en todas las plantillas existentes (fuera de alcance de esta tarea,
# documentado como mejora futura en docs/SECURITY.md).

PERMISSIONS_POLICY = (
    'geolocation=(), camera=(), microphone=(), payment=(), usb=(), '
    'magnetometer=(), gyroscope=(), accelerometer=(), interest-cohort=()'
)


def init_security_headers(app) -> None:
    # Flask llama a los after_request en orden inverso al de registro, y
    # Talisman ya fija su propio Permissions-Policy por default — este
    # hook se registra ANTES de talisman.init_app() para que se ejecute
    # DESPUÉS y su valor gane.
    @app.after_request
    def _permissions_policy(response: Response) -> Response:
        response.headers['Permissions-Policy'] = PERMISSIONS_POLICY
        return response

    talisman.init_app(
        app,
        content_security_policy=CONTENT_SECURITY_POLICY,
        force_https=app.config.get('TALISMAN_FORCE_HTTPS', False),
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        referrer_policy='strict-origin-when-cross-origin',
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', True),
        x_content_type_options=True,
        frame_options='DENY',
    )
