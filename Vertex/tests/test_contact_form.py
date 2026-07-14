import re
import time

from app.models.contacto import Contacto


def _get_form_fields(client):
    r = client.get('/contacto')
    html = r.data.decode('utf-8')
    form_ts = re.search(r'name="form_ts"[^>]*value="([^"]+)"', html).group(1)
    return form_ts


def _post_contacto(client, servicio_id, form_ts, **overrides):
    data = dict(
        website='',
        form_ts=form_ts,
        nombre='Cliente de prueba',
        empresa='Mi empresa',
        email='cliente@example.com',
        telefono='',
        servicio_id=str(servicio_id),
        rango_presupuesto_id='0',
        descripcion_proyecto='Necesito un sitio web para mi negocio.',
    )
    data.update(overrides)
    return client.post('/contacto/enviar', data=data, follow_redirects=True)


def test_get_contacto_incluye_campos_antibot(client, servicio):
    r = client.get('/contacto')
    assert r.status_code == 200
    assert b'form_ts' in r.data
    assert b'name="website"' in r.data


def test_envio_sin_nombre_es_rechazado(client, servicio, app):
    app.config['CONTACT_MIN_SECONDS'] = 0
    form_ts = _get_form_fields(client)
    r = _post_contacto(client, servicio, form_ts, nombre='')
    assert r.status_code == 200
    with app.app_context():
        assert Contacto.query.count() == 0


def test_envio_servicio_inexistente_es_rechazado(client, servicio, app):
    app.config['CONTACT_MIN_SECONDS'] = 0
    form_ts = _get_form_fields(client)
    r = _post_contacto(client, 9999, form_ts)
    assert r.status_code == 200
    with app.app_context():
        assert Contacto.query.count() == 0


def test_honeypot_descarta_silenciosamente(client, servicio, app):
    app.config['CONTACT_MIN_SECONDS'] = 0
    form_ts = _get_form_fields(client)
    r = _post_contacto(client, servicio, form_ts, website='http://spam.example.com')
    # Responde como si fuera éxito (no delata al bot) pero no guarda nada.
    assert r.status_code == 200
    with app.app_context():
        assert Contacto.query.count() == 0


def test_envio_demasiado_rapido_se_descarta(client, servicio, app):
    app.config['CONTACT_MIN_SECONDS'] = 5
    form_ts = _get_form_fields(client)
    r = _post_contacto(client, servicio, form_ts)  # sin esperar
    assert r.status_code == 200
    with app.app_context():
        assert Contacto.query.count() == 0


def test_envio_legitimo_se_guarda_sanitizado(client, servicio, app):
    app.config['CONTACT_MIN_SECONDS'] = 0
    form_ts = _get_form_fields(client)
    time.sleep(0.05)
    r = _post_contacto(
        client, servicio, form_ts,
        nombre='<script>alert(1)</script>Juan',
        descripcion_proyecto='<img src=x onerror=alert(1)>Quiero un sitio web',
    )
    assert r.status_code == 200
    with app.app_context():
        contactos = Contacto.query.all()
        assert len(contactos) == 1
        contacto = contactos[0]
        # El HTML/JS se eliminó por completo (bleach) — no queda ni el tag.
        assert '<script>' not in contacto.nombre
        assert 'alert(1)' not in contacto.nombre or '<' not in contacto.nombre
        assert '<img' not in contacto.descripcion_proyecto
        assert 'Juan' in contacto.nombre
        assert contacto.ip is not None
        assert contacto.estado == 'nuevo'


def test_sql_injection_no_rompe_ni_se_ejecuta(client, servicio, app):
    """El ORM parametriza todo — una cadena tipo SQLi se guarda como
    texto literal, no se interpreta como SQL."""
    app.config['CONTACT_MIN_SECONDS'] = 0
    form_ts = _get_form_fields(client)
    payload = "Robert'); DROP TABLE contactos;--"
    r = _post_contacto(client, servicio, form_ts, nombre=payload)
    assert r.status_code == 200
    with app.app_context():
        contactos = Contacto.query.all()
        assert len(contactos) == 1
        assert 'DROP TABLE' in contactos[0].nombre  # se guardó como texto plano, inofensivo
