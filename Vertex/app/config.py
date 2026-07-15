"""Configuración de la aplicación por entorno.

Nunca se ponen credenciales reales aquí — todo viene de variables de
entorno (ver .env.example). Las clases solo definen defaults seguros
para desarrollo/pruebas.
"""
import os

from sqlalchemy.pool import StaticPool


def _bool_env(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'cambia-esto-en-produccion')

    # Dominio canónico del sitio (sin www, https, sin barra final). Se usa
    # para generar <link rel="canonical">, og:url y las URLs absolutas de SEO.
    SITE_URL = os.getenv('SITE_URL', 'https://asvertex.store')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///pixelforge.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # Flask-Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = _bool_env('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'hola@asvertex.com')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'hola@asvertex.com')

    # Flask-WTF / CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Flask-Limiter. En producción se debe definir REDIS_URL explícitamente;
    # si no está presente (ej. desarrollo local sin Redis instalado) se usa
    # almacenamiento en memoria del proceso como fallback razonable.
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True
    CONTACT_RATE_LIMITS = '5 per minute;20 per hour;100 per day'

    # Bloqueo automático de IPs
    RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK = int(os.getenv('RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK', 3))
    RATE_LIMIT_BLOCK_HOURS = int(os.getenv('RATE_LIMIT_BLOCK_HOURS', 24))

    # Login admin
    LOGIN_MAX_ATTEMPTS = int(os.getenv('LOGIN_MAX_ATTEMPTS', 5))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv('LOGIN_LOCKOUT_MINUTES', 15))

    # Antibot del formulario de contacto
    CONTACT_MIN_SECONDS = int(os.getenv('CONTACT_MIN_SECONDS', 5))
    CONTACT_HONEYPOT_FIELD = 'website'

    # Cuántos proxies confiables hay delante de la app (Cloudflare -> Nginx -> Flask == 2)
    TRUSTED_PROXY_COUNT = int(os.getenv('TRUSTED_PROXY_COUNT', 1))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False
    AUTO_CREATE_DB = True  # comodidad en dev; en prod el esquema lo maneja Alembic


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # StaticPool: una sola conexión compartida por todos los hilos, para
    # que el hilo de background de email_service vea las mismas tablas
    # que el hilo principal de la petición durante los tests.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False},
    }
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = 'memory://'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False
    CONTACT_MIN_SECONDS = 5
    AUTO_CREATE_DB = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Cloudflare ya redirige HTTP -> HTTPS ("Always Use HTTPS"); si Talisman
    # también fuerza el redirect se puede generar un loop en modo Flexible.
    TALISMAN_FORCE_HTTPS = False
    AUTO_CREATE_DB = False  # el esquema se aplica con `flask db upgrade`


CONFIG_BY_NAME = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return CONFIG_BY_NAME.get(env, DevelopmentConfig)
