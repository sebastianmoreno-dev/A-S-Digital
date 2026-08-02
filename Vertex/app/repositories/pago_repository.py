"""Acceso a datos de planes de pago y parcialidades."""
from datetime import date

from app.models.future.crm import Cliente
from app.models.pagos import Parcialidad, PlanPago


def plan_activo_de_cliente(cliente_id: int):
    """Plan activo del cliente (se maneja uno por cliente)."""
    return (PlanPago.query
            .filter_by(cliente_id=cliente_id, activo=True)
            .order_by(PlanPago.creado_en.desc())
            .first())


def obtener_plan(plan_id: int):
    return PlanPago.query.get(plan_id)


def obtener_parcialidad(parcialidad_id: int):
    return Parcialidad.query.get(parcialidad_id)


def _pendientes_query():
    return (Parcialidad.query
            .join(PlanPago, Parcialidad.plan_id == PlanPago.id)
            .filter(Parcialidad.estado != 'pagada', PlanPago.activo.is_(True)))


def proximas_parcialidades(limite: int = 5):
    """Parcialidades pendientes más próximas a vencer (global, para el Dashboard)."""
    return (_pendientes_query()
            .order_by(Parcialidad.fecha_vencimiento.asc())
            .limit(limite)
            .all())


def parcialidades_vencidas():
    """Parcialidades pendientes con fecha ya pasada (global)."""
    return (_pendientes_query()
            .filter(Parcialidad.fecha_vencimiento < date.today())
            .order_by(Parcialidad.fecha_vencimiento.asc())
            .all())
