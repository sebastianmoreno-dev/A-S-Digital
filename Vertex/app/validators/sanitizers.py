"""Sanitización de entradas de usuario — nunca se confía en el frontend.

Todo campo de texto libre que vaya a la base de datos pasa por aquí
antes de guardarse, como defensa en profundidad además del autoescape
de Jinja2 al renderizar.
"""
import bleach

# Ningún campo del sitio necesita HTML: se limpia todo por completo.
_ALLOWED_TAGS: list[str] = []
_ALLOWED_ATTRS: dict = {}


def strip_html(value: str | None) -> str:
    """Elimina cualquier etiqueta/atributo HTML o JavaScript del texto."""
    if not value:
        return ''
    cleaned = bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
    return cleaned.strip()


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ''
    return ' '.join(value.split())
