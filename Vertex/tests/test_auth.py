import re

from app.models.admin import IntentoLogin


def _csrf(client, url):
    r = client.get(url)
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r.data.decode())
    return match.group(1) if match else ''


def test_login_credenciales_invalidas_no_autentica(client, admin_credenciales):
    email, _ = admin_credenciales
    r = client.post('/admin/login', data=dict(
        csrf_token=_csrf(client, '/admin/login'), email=email, password='incorrecta',
    ), follow_redirects=True)
    assert r.status_code == 200

    r = client.get('/admin/')
    assert r.status_code == 302  # redirige a login — no autenticado
    assert '/admin/login' in r.headers['Location']


def test_login_credenciales_validas_autentica(client, admin_credenciales):
    email, password = admin_credenciales
    r = client.post('/admin/login', data=dict(
        csrf_token=_csrf(client, '/admin/login'), email=email, password=password,
    ), follow_redirects=True)
    assert r.status_code == 200

    r = client.get('/admin/')
    assert r.status_code == 200


def test_login_registra_intentos_en_bitacora(client, app, admin_credenciales):
    email, _ = admin_credenciales
    client.post('/admin/login', data=dict(
        csrf_token=_csrf(client, '/admin/login'), email=email, password='mala',
    ))
    with app.app_context():
        intento = IntentoLogin.query.filter_by(email_intentado=email).first()
        assert intento is not None
        assert intento.exitoso is False


def test_lockout_tras_intentos_fallidos_repetidos(client, app, admin_credenciales):
    email, password = admin_credenciales
    app.config['LOGIN_MAX_ATTEMPTS'] = 3

    for _ in range(3):
        client.post('/admin/login', data=dict(
            csrf_token=_csrf(client, '/admin/login'), email=email, password='mala',
        ))

    # Aun con la contraseña correcta, la cuenta debe estar bloqueada temporalmente.
    r = client.post('/admin/login', data=dict(
        csrf_token=_csrf(client, '/admin/login'), email=email, password=password,
    ), follow_redirects=True)
    assert b'bloqueada' in r.data.lower() or b'Demasiados intentos' in r.data

    r = client.get('/admin/')
    assert r.status_code == 302  # sigue sin poder entrar
