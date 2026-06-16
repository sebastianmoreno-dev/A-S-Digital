from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

db   = SQLAlchemy()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────────
    app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'cambia-esto-en-produccion')
    app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///pixelforge.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Flask-Mail
    app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER',   'smtp.gmail.com')
    app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS']        = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'hola@pixelforgestudio.mx')

    # ── Extensiones ────────────────────────────────────────────────
    db.init_app(app)
    mail.init_app(app)

    # ── Blueprints ─────────────────────────────────────────────────
    from app.routes.main    import main_bp
    from app.routes.contact import contact_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)

    # ── Crear tablas si no existen ─────────────────────────────────
    with app.app_context():
        db.create_all()

    return app
