"""Instancias únicas de extensiones Flask, creadas sin app (patrón factory).

Se importan desde aquí en todo el proyecto para evitar imports
circulares con app/__init__.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_login import LoginManager
from flask_talisman import Talisman

from app.utils.ip import get_client_ip

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()
talisman = Talisman()

# IP real detrás de Cloudflare (CF-Connecting-IP), no request.remote_addr directo.
limiter = Limiter(key_func=get_client_ip)
