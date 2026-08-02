"""Fase 1: alta manual de leads, filtro por origen, categorías de eventos
y toggle inline del catálogo."""
from app.extensions import db as _db
from app.models.catalog import Servicio
from app.models.contacto import Contacto
from app.models.security import BitacoraEvento


def _login(client, admin_credenciales):
    email, password = admin_credenciales
    return client.post('/admin/login', data=dict(email=email, password=password),
                       follow_redirects=True)


def test_lead_del_formulario_queda_como_formulario_web(app, db, servicio):
    """El default del modelo marca los leads sin origen explícito."""
    with app.app_context():
        c = Contacto(nombre='Web', email='web@x.com', servicio_id=servicio,
                     descripcion_proyecto='hola', ip='1.2.3.4', estado='nuevo')
        _db.session.add(c)
        _db.session.commit()
        assert c.origen == 'formulario_web'


def test_crear_lead_manual(client, app, admin_credenciales, servicio, rango):
    _login(client, admin_credenciales)
    r = client.post('/admin/leads/nuevo', data=dict(
        nombre='Referido Uno', email='ref@x.com', telefono='555',
        servicio_id=servicio, rango_presupuesto_id=rango,
        origen='referido', estado='ganado', nota='Llegó por un conocido',
    ), follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        lead = Contacto.query.filter_by(email='ref@x.com').first()
        assert lead is not None
        assert lead.origen == 'referido'
        assert lead.estado == 'ganado'
        assert lead.descripcion_proyecto == 'Llegó por un conocido'
        # Se registró el evento de negocio.
        evt = BitacoraEvento.query.filter_by(tipo_evento='lead_creado_manual').first()
        assert evt is not None


def test_filtro_por_origen_en_listado(client, app, admin_credenciales, servicio):
    with app.app_context():
        for email, origen in [('a@x.com', 'referido'), ('b@x.com', 'redes_sociales')]:
            _db.session.add(Contacto(nombre='N', email=email, servicio_id=servicio,
                                     descripcion_proyecto='d', ip='1.1.1.1',
                                     estado='nuevo', origen=origen))
        _db.session.commit()

    _login(client, admin_credenciales)
    r = client.get('/admin/leads?origen=referido')
    assert r.status_code == 200
    assert b'a@x.com' in r.data
    assert b'b@x.com' not in r.data


def test_dashboard_separa_negocio_y_seguridad(client, app, admin_credenciales):
    with app.app_context():
        _db.session.add(BitacoraEvento(tipo_evento='contacto_exitoso', nivel='info',
                                       descripcion='negocio', ip='9.9.9.9'))
        _db.session.add(BitacoraEvento(tipo_evento='login', nivel='info',
                                       descripcion='seguridad', ip='8.8.8.8'))
        _db.session.commit()

    _login(client, admin_credenciales)

    # Negocio (default): no muestra el evento de seguridad ni su IP.
    r = client.get('/admin/?cat=negocio')
    assert b'contacto exitoso' in r.data or b'contacto_exitoso' in r.data
    assert b'8.8.8.8' not in r.data

    # Seguridad: muestra login y su IP.
    r = client.get('/admin/?cat=seguridad')
    assert b'8.8.8.8' in r.data


def test_toggle_servicio_invierte_activo(client, app, admin_credenciales, servicio):
    _login(client, admin_credenciales)
    r = client.post(f'/admin/servicios/{servicio}/toggle', follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        s = Servicio.query.get(servicio)
        assert s.activo is False  # el fixture lo crea activo=True
