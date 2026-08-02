"""Fase 2 — flujo de clientes y planes de pago (con BD)."""
from datetime import date
from decimal import Decimal

from app.extensions import db as _db
from app.models.contacto import Contacto
from app.models.future.crm import Cliente, ProyectoCliente
from app.models.pagos import Parcialidad, PlanPago
from app.services import pagos_service


def _login(client, admin_credenciales):
    email, password = admin_credenciales
    return client.post('/admin/login', data=dict(email=email, password=password),
                       follow_redirects=True)


def _lead_ganado(servicio, email='ganado@x.com'):
    c = Contacto(nombre='Marca X', email=email, servicio_id=servicio,
                 descripcion_proyecto='Dos sitios', ip='1.2.3.4', estado='ganado',
                 origen='referido')
    _db.session.add(c)
    _db.session.commit()
    return c.id


def test_clientes_requiere_autenticacion(client):
    r = client.get('/admin/clientes')
    assert r.status_code == 302
    assert '/admin/login' in r.headers['Location']


def test_convertir_lead_crea_cliente_y_proyecto(client, app, admin_credenciales, servicio):
    with app.app_context():
        lead_id = _lead_ganado(servicio)

    _login(client, admin_credenciales)
    r = client.post(f'/admin/leads/{lead_id}/convertir', follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(creado_desde_contacto_id=lead_id).first()
        assert cliente is not None
        proyectos = ProyectoCliente.query.filter_by(cliente_id=cliente.id).all()
        assert len(proyectos) == 1
        assert proyectos[0].contacto_id == lead_id


def test_crear_plan_genera_24_parcialidades_caso_real(client, app, admin_credenciales):
    with app.app_context():
        cliente = Cliente(nombre='Streetwear')
        _db.session.add(cliente)
        _db.session.commit()
        cid = cliente.id

    _login(client, admin_credenciales)
    r = client.post(f'/admin/clientes/{cid}/plan', data=dict(
        monto_total='12000.00', frecuencia='quincenal_15_fin',
        fecha_inicio='2026-08-31', num_parcialidades='24',
    ), follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        plan = PlanPago.query.filter_by(cliente_id=cid).first()
        assert plan is not None
        parts = Parcialidad.query.filter_by(plan_id=plan.id).order_by(Parcialidad.numero).all()
        assert len(parts) == 24
        assert parts[0].fecha_vencimiento == date(2026, 8, 31)
        assert parts[1].fecha_vencimiento == date(2026, 9, 15)
        assert parts[-1].fecha_vencimiento == date(2027, 8, 15)
        # La suma de montos cuadra exactamente con el total.
        assert sum(Decimal(str(p.monto)) for p in parts) == Decimal('12000.00')


def test_crear_plan_por_fecha_fin_calcula_num(client, app, admin_credenciales):
    with app.app_context():
        cliente = Cliente(nombre='Cliente Fin')
        _db.session.add(cliente)
        _db.session.commit()
        cid = cliente.id

    _login(client, admin_credenciales)
    client.post(f'/admin/clientes/{cid}/plan', data=dict(
        monto_total='1000.00', frecuencia='quincenal_15_fin',
        fecha_inicio='2026-08-31', fecha_fin='2026-09-30',
    ), follow_redirects=True)

    with app.app_context():
        plan = PlanPago.query.filter_by(cliente_id=cid).first()
        # 31-ago, 15-sep, 30-sep = 3 parcialidades
        assert plan.num_parcialidades == 3
        assert Parcialidad.query.filter_by(plan_id=plan.id).count() == 3


def test_marcar_pagada_actualiza_resumen(client, app, admin_credenciales):
    with app.app_context():
        cliente = Cliente(nombre='Pagos')
        _db.session.add(cliente)
        _db.session.commit()
        cid = cliente.id
        plan = pagos_service.crear_plan(cid, monto_total=Decimal('1000.00'),
                                        frecuencia='quincenal_15_fin',
                                        fecha_inicio=date(2026, 8, 31), num_parcialidades=4)
        primera_id = plan.parcialidades[0].id

    _login(client, admin_credenciales)
    r = client.post(f'/admin/parcialidades/{primera_id}/pagar',
                    data=dict(fecha_pago='2026-08-31'), follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        p = Parcialidad.query.get(primera_id)
        assert p.estado == 'pagada'
        assert p.fecha_pago == date(2026, 8, 31)
        resumen = pagos_service.resumen_financiero(p.plan)
        assert resumen['pagado'] == Decimal('250.00')
        assert resumen['pendiente'] == Decimal('750.00')


def test_regenerar_plan_bloqueado_si_hay_pagos(client, app, admin_credenciales):
    with app.app_context():
        cliente = Cliente(nombre='Con Pago')
        _db.session.add(cliente)
        _db.session.commit()
        cid = cliente.id
        plan = pagos_service.crear_plan(cid, monto_total=Decimal('1000.00'),
                                        frecuencia='quincenal_15_fin',
                                        fecha_inicio=date(2026, 8, 31), num_parcialidades=4)
        pagos_service.marcar_pagada(plan.parcialidades[0])

    _login(client, admin_credenciales)
    r = client.post(f'/admin/clientes/{cid}/plan', data=dict(
        monto_total='2000.00', frecuencia='quincenal_15_fin',
        fecha_inicio='2026-08-31', num_parcialidades='10',
    ), follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        plan = PlanPago.query.filter_by(cliente_id=cid).first()
        # No se regeneró: sigue con 4 parcialidades y monto original.
        assert plan.num_parcialidades == 4
        assert Decimal(str(plan.monto_total)) == Decimal('1000.00')
