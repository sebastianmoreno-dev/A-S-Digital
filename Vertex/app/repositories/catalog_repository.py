"""Acceso a datos del catálogo de servicios y rangos de presupuesto."""
from app.extensions import db
from app.models.catalog import RangoPresupuesto, Servicio


def listar_servicios_activos():
    return Servicio.query.filter_by(activo=True).order_by(Servicio.orden, Servicio.nombre).all()


def listar_todos_servicios():
    return Servicio.query.order_by(Servicio.orden, Servicio.nombre).all()


def obtener_servicio(servicio_id: int):
    return Servicio.query.get(servicio_id)


def obtener_servicio_activo(servicio_id: int):
    return Servicio.query.filter_by(id=servicio_id, activo=True).first()


def guardar_servicio(servicio: Servicio):
    db.session.add(servicio)
    db.session.commit()
    return servicio


def listar_rangos_activos():
    return RangoPresupuesto.query.filter_by(activo=True).order_by(RangoPresupuesto.orden).all()


def listar_todos_rangos():
    return RangoPresupuesto.query.order_by(RangoPresupuesto.orden).all()


def obtener_rango(rango_id: int):
    return RangoPresupuesto.query.get(rango_id)


def obtener_rango_activo(rango_id: int):
    return RangoPresupuesto.query.filter_by(id=rango_id, activo=True).first()


def guardar_rango(rango: RangoPresupuesto):
    db.session.add(rango)
    db.session.commit()
    return rango
