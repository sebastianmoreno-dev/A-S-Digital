import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models.catalog import Servicio
from app.models.security import ListaNegraIP, RateLimitViolacion


class RateLimitedConfig(TestingConfig):
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = 'memory://'
    CONTACT_RATE_LIMITS = '3 per minute'
    RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK = 2


@pytest.fixture()
def rl_app():
    application = create_app(RateLimitedConfig)
    with application.app_context():
        _db.create_all()
        _db.session.add(Servicio(clave='frontend', nombre='Frontend', activo=True))
        _db.session.commit()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def rl_client(rl_app):
    return rl_app.test_client()


def _post_minimo(client):
    return client.post('/contacto/enviar', data=dict(
        website='', form_ts='', nombre='X', email='x@test.com',
        servicio_id='1', rango_presupuesto_id='0', descripcion_proyecto='x',
    ))


def test_excede_limite_devuelve_429(rl_client):
    for _ in range(3):
        r = _post_minimo(rl_client)
        assert r.status_code in (200, 302)

    r = _post_minimo(rl_client)
    assert r.status_code == 429


def test_violaciones_repetidas_bloquean_la_ip_automaticamente(rl_app, rl_client):
    # 3/min permitidas; con RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK=2, la
    # segunda vez que se excede el límite debe autobloquear la IP.
    for _ in range(3):
        _post_minimo(rl_client)

    r1 = _post_minimo(rl_client)  # 1ra violación
    assert r1.status_code == 429

    r2 = _post_minimo(rl_client)  # 2da violación -> debe disparar el bloqueo
    assert r2.status_code in (429, 403)

    with rl_app.app_context():
        violaciones = RateLimitViolacion.query.count()
        assert violaciones >= 2
        bloqueo = ListaNegraIP.query.filter_by(ip='127.0.0.1', activo=True).first()
        assert bloqueo is not None
        assert bloqueo.esta_vigente()

    # Una IP bloqueada debe recibir 403 incluso en una ruta distinta.
    r3 = rl_client.get('/')
    assert r3.status_code == 403
