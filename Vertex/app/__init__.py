from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import get_config
from app.extensions import csrf, db, login_manager, mail, migrate


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    # Cloudflare -> (Nginx/gunicorn) -> Flask: confía en N proxies para
    # X-Forwarded-For / X-Forwarded-Proto (necesario para HTTPS/IP reales).
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=app.config['TRUSTED_PROXY_COUNT'],
        x_proto=app.config['TRUSTED_PROXY_COUNT'],
        x_host=0,
        x_port=0,
    )

    _init_extensions(app)
    _register_blueprints(app)
    _init_translations(app)

    # En producción el esquema se gestiona con `flask db upgrade`
    # (Alembic); create_all() aquí es solo comodidad para dev/tests,
    # donde no siempre hay migraciones corridas todavía.
    if app.config.get('AUTO_CREATE_DB'):
        with app.app_context():
            db.create_all()

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Inicia sesión para continuar.'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_admin(admin_id):
        from app.models.admin import Administrador
        return Administrador.query.get(int(admin_id))

    # Middlewares que dependen de extensiones ya inicializadas
    from app.middlewares.rate_limit import init_rate_limiting
    from app.middlewares.security_headers import init_security_headers

    init_rate_limiting(app)
    init_security_headers(app)


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.admin import admin_bp
    from app.blueprints.contact import contact_bp
    from app.blueprints.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(admin_bp)


def _init_translations(app: Flask) -> None:
    from app.translations import t

    @app.context_processor
    def inject_translator():
        return dict(t=t)
