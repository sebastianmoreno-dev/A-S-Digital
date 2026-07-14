import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models.admin import Administrador, Permiso, Rol
from app.models.catalog import RangoPresupuesto, Servicio
from app.utils.security import hash_password


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    yield application


@pytest.fixture(autouse=True)
def _no_real_emails(monkeypatch):
    """Los tests nunca deben intentar mandar correos reales — se
    reemplaza el envío en background por un no-op."""
    monkeypatch.setattr('app.services.contact_service.email_service.enviar_async', lambda *a, **k: None)


@pytest.fixture()
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app, db):
    return app.test_client()


@pytest.fixture()
def servicio(app, db):
    with app.app_context():
        s = Servicio(clave='frontend', nombre='Frontend', activo=True, precio_desde=5000)
        _db.session.add(s)
        _db.session.commit()
        return s.id


@pytest.fixture()
def rango(app, db):
    with app.app_context():
        r = RangoPresupuesto(clave='5k-10k', etiqueta='$5,000 - $10,000', activo=True)
        _db.session.add(r)
        _db.session.commit()
        return r.id


@pytest.fixture()
def rol_admin(app, db):
    with app.app_context():
        rol = Rol(nombre='Administrador')
        _db.session.add(rol)
        _db.session.flush()
        permisos = [
            Permiso(clave='leads.view'),
            Permiso(clave='leads.edit'),
            Permiso(clave='catalogo.manage'),
            Permiso(clave='config.manage'),
        ]
        _db.session.add_all(permisos)
        _db.session.flush()
        rol.permisos = permisos
        _db.session.commit()
        return rol.id


@pytest.fixture()
def admin_credenciales(app, db, rol_admin):
    email = 'admin@test.com'
    password = 'ClaveSegura123!'
    with app.app_context():
        admin = Administrador(
            nombre='Admin Test', email=email, password_hash=hash_password(password),
            rol_id=rol_admin, activo=True,
        )
        _db.session.add(admin)
        _db.session.commit()
    return email, password
