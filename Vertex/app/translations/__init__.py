"""Traducciones del sitio, cargadas desde JSON.

Cada idioma vive en su propio archivo (es.json / en.json) dentro de este
paquete. Para agregar un idioma nuevo basta con crear su .json y sumarlo
a LANGUAGES — no hay que tocar templates ni más código Python.

Los .json son diccionarios planos clave → texto, con las claves
namespaceadas por página ("index.hero.p", "form.nombre", ...).
"""
import json
from pathlib import Path

_DIR = Path(__file__).parent

LANGUAGES = ('es', 'en')
DEFAULT_LANG = 'es'

TRANSLATIONS = {
    lang: json.loads((_DIR / f'{lang}.json').read_text(encoding='utf-8'))
    for lang in LANGUAGES
}


def t(key):
    """Texto para `key` en el idioma de la sesión.

    Si la clave no existe en el idioma activo cae al idioma por defecto,
    y en último caso devuelve la clave misma (así una clave faltante se
    ve en pantalla en vez de romper el render).
    """
    from flask import session
    lang = session.get('lang', DEFAULT_LANG)
    catalogo = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANG])
    valor = catalogo.get(key)
    if valor is None:
        valor = TRANSLATIONS[DEFAULT_LANG].get(key, key)
    return valor


class LazyT:
    """Texto perezoso: resuelve t(key) hasta convertirse a str.

    Necesario donde el texto se define fuera de un request (p. ej. los
    mensajes de los validadores WTForms, que viven a nivel de clase):
    ahí todavía no existe sesión, así que se guarda la clave y se
    traduce cuando el mensaje realmente se muestra.
    """
    __slots__ = ('key',)

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return t(self.key)

    def __repr__(self):
        return f'LazyT({self.key!r})'

    def __mod__(self, params):
        return str(self) % params


def lazy_t(key):
    return LazyT(key)
