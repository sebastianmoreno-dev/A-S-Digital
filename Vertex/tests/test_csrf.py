import re

import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models.catalog import Servicio


class CsrfEnabledConfig(TestingConfig):
    WTF_CSRF_ENABLED = True


@pytest.fixture()
def csrf_app():
    application = create_app(CsrfEnabledConfig)
    with application.app_context():
        _db.create_all()
        _db.session.add(Servicio(clave='frontend', nombre='Frontend', activo=True))
        _db.session.commit()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_post_sin_csrf_token_es_rechazado(csrf_client):
    r = csrf_client.get('/contacto')
    form_ts = re.search(r'name="form_ts"[^>]*value="([^"]+)"', r.data.decode()).group(1)

    r = csrf_client.post('/contacto/enviar', data=dict(
        # csrf_token deliberadamente omitido
        website='', form_ts=form_ts, nombre='Juan', email='juan@test.com',
        servicio_id='1', rango_presupuesto_id='0', descripcion_proyecto='Hola',
    ))
    assert r.status_code == 400


def test_post_con_csrf_token_valido_pasa_la_proteccion(csrf_client):
    r = csrf_client.get('/contacto')
    html = r.data.decode()
    csrf_token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html).group(1)
    form_ts = re.search(r'name="form_ts"[^>]*value="([^"]+)"', html).group(1)

    r = csrf_client.post('/contacto/enviar', data=dict(
        csrf_token=csrf_token, website='', form_ts=form_ts,
        nombre='Juan', email='juan@test.com',
        servicio_id='1', rango_presupuesto_id='0', descripcion_proyecto='Hola',
    ))
    # No debe ser 400 (CSRF ok); puede redirigir por el chequeo de tiempo mínimo, y eso está bien.
    assert r.status_code != 400
