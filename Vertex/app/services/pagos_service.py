"""Lógica de planes de pago: cálculo de fechas de vencimiento, reparto de
montos y operaciones sobre parcialidades.

Maneja dinero real: los cálculos de fechas y montos están cubiertos por
tests (tests/test_pagos_calc.py). El reparto de montos usa Decimal en
centavos para que la suma de las parcialidades sea EXACTAMENTE el total.
"""
import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.extensions import db
from app.middlewares.request_logger import log_evento
from app.models.pagos import Parcialidad, PlanPago

CENTAVO = Decimal('0.01')


class PlanInvalido(Exception):
    """Datos del plan inconsistentes (frecuencia no soportada, num inválido…)."""


# ── Cálculo de fechas ────────────────────────────────────────────────

def _ultimo_dia(anio: int, mes: int) -> int:
    return calendar.monthrange(anio, mes)[1]


def _normaliza_inicio_quincenal(d: date) -> date:
    """El esquema quincenal solo vence los días 15 y último de cada mes.
    Si la fecha de inicio no cae en una de esas anclas, se ajusta a la más
    cercana dentro del mismo mes (≤15 → el 15; >15 → fin de mes)."""
    ultimo = _ultimo_dia(d.year, d.month)
    if d.day == 15 or d.day == ultimo:
        return d
    return date(d.year, d.month, 15) if d.day < 15 else date(d.year, d.month, ultimo)


def _siguiente_quincenal(d: date) -> date:
    """Dada una ancla (día 15 o último del mes), devuelve la siguiente:
    desde el 15 → último día del MISMO mes; desde fin de mes → 15 del SIGUIENTE."""
    if d.day == 15:
        return date(d.year, d.month, _ultimo_dia(d.year, d.month))
    if d.month == 12:
        return date(d.year + 1, 1, 15)
    return date(d.year, d.month + 1, 15)


def generar_vencimientos(frecuencia: str, fecha_inicio: date, num: int) -> list[date]:
    """Lista de `num` fechas de vencimiento según la frecuencia."""
    if num < 1:
        raise PlanInvalido('El número de parcialidades debe ser al menos 1.')
    if frecuencia != 'quincenal_15_fin':
        raise PlanInvalido(f'Frecuencia no soportada todavía: {frecuencia}')

    d = _normaliza_inicio_quincenal(fecha_inicio)
    fechas = []
    for _ in range(num):
        fechas.append(d)
        d = _siguiente_quincenal(d)
    return fechas


def contar_vencimientos(frecuencia: str, inicio: date, fin: date) -> int:
    """Cuántas anclas caen en [inicio, fin] — para el modo 'inicio + fin'."""
    if frecuencia != 'quincenal_15_fin':
        raise PlanInvalido(f'Frecuencia no soportada todavía: {frecuencia}')
    if fin < inicio:
        return 0
    d = _normaliza_inicio_quincenal(inicio)
    n = 0
    while d <= fin and n < 1000:   # tope de seguridad anti-bucle
        n += 1
        d = _siguiente_quincenal(d)
    return n


# ── Reparto de montos ────────────────────────────────────────────────

def partir_monto(total, num: int) -> list[Decimal]:
    """Divide `total` en `num` montos (Decimal, 2 decimales) cuya suma es
    EXACTAMENTE el total. El sobrante en centavos se reparte en las primeras
    parcialidades (así ninguna difiere más de un centavo del resto)."""
    if num < 1:
        raise PlanInvalido('El número de parcialidades debe ser al menos 1.')
    total_cents = int((Decimal(str(total)) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    base, resto = divmod(total_cents, num)
    return [ (Decimal(base + (1 if i < resto else 0)) / 100).quantize(CENTAVO) for i in range(num) ]


# ── Resumen financiero ───────────────────────────────────────────────

def resumen_financiero(plan: PlanPago) -> dict:
    """Total, pagado, pendiente, próxima fecha y nº de vencidas de un plan."""
    total = Decimal(str(plan.monto_total))
    pagado = sum((Decimal(str(p.monto)) for p in plan.parcialidades if p.estado == 'pagada'), Decimal('0'))
    pendientes = [p for p in plan.parcialidades if p.estado != 'pagada']
    vencidas = [p for p in pendientes if p.esta_vencida]
    proxima = min((p.fecha_vencimiento for p in pendientes), default=None)
    return {
        'total': total,
        'pagado': pagado,
        'pendiente': total - pagado,
        'proxima_fecha': proxima,
        'num_vencidas': len(vencidas),
        'num_pendientes': len(pendientes),
        'num_total': len(plan.parcialidades),
    }


# ── Operaciones de persistencia ──────────────────────────────────────

def crear_plan(cliente_id: int, *, monto_total, frecuencia: str, fecha_inicio: date,
               num_parcialidades: int, moneda: str = 'MXN', notas: str | None = None,
               admin_id: int | None = None) -> PlanPago:
    """Crea el plan y genera sus parcialidades (fechas + montos)."""
    fechas = generar_vencimientos(frecuencia, fecha_inicio, num_parcialidades)
    montos = partir_monto(monto_total, num_parcialidades)

    plan = PlanPago(
        cliente_id=cliente_id, monto_total=monto_total, moneda=moneda,
        frecuencia=frecuencia, fecha_inicio=fechas[0], num_parcialidades=num_parcialidades,
        notas=notas, activo=True,
    )
    db.session.add(plan)
    db.session.flush()  # obtiene plan.id

    for i, (f, m) in enumerate(zip(fechas, montos), start=1):
        db.session.add(Parcialidad(plan_id=plan.id, numero=i, fecha_vencimiento=f, monto=m))

    db.session.commit()
    log_evento('plan_pago_creado', nivel='info',
               descripcion=f'Plan de pago cliente #{cliente_id}: {num_parcialidades} parcialidades, total ${monto_total}',
               administrador_id=admin_id)
    return plan


def hay_pagos_registrados(plan: PlanPago) -> bool:
    return any(p.estado == 'pagada' for p in plan.parcialidades)


def regenerar_plan(plan: PlanPago, *, monto_total, frecuencia: str, fecha_inicio: date,
                   num_parcialidades: int, moneda: str = 'MXN', notas: str | None = None,
                   admin_id: int | None = None) -> PlanPago:
    """Reemplaza las parcialidades de un plan existente. El caller debe haber
    verificado con `hay_pagos_registrados` antes de permitirlo."""
    fechas = generar_vencimientos(frecuencia, fecha_inicio, num_parcialidades)
    montos = partir_monto(monto_total, num_parcialidades)

    Parcialidad.query.filter_by(plan_id=plan.id).delete()
    plan.monto_total = monto_total
    plan.moneda = moneda
    plan.frecuencia = frecuencia
    plan.fecha_inicio = fechas[0]
    plan.num_parcialidades = num_parcialidades
    plan.notas = notas
    for i, (f, m) in enumerate(zip(fechas, montos), start=1):
        db.session.add(Parcialidad(plan_id=plan.id, numero=i, fecha_vencimiento=f, monto=m))

    db.session.commit()
    log_evento('plan_pago_regenerado', nivel='warning',
               descripcion=f'Plan de pago cliente #{plan.cliente_id} regenerado: {num_parcialidades} parcialidades',
               administrador_id=admin_id)
    return plan


def marcar_pagada(parcialidad: Parcialidad, *, fecha_pago: date | None = None,
                  admin_id: int | None = None) -> Parcialidad:
    parcialidad.estado = 'pagada'
    parcialidad.fecha_pago = fecha_pago or date.today()
    parcialidad.pagada_por_admin_id = admin_id
    db.session.commit()
    log_evento('parcialidad_pagada', nivel='info',
               descripcion=f'Parcialidad #{parcialidad.numero} (plan {parcialidad.plan_id}) marcada pagada — ${parcialidad.monto}',
               administrador_id=admin_id)
    return parcialidad


def desmarcar_pagada(parcialidad: Parcialidad, *, admin_id: int | None = None) -> Parcialidad:
    """Revierte un pago marcado por error."""
    parcialidad.estado = 'pendiente'
    parcialidad.fecha_pago = None
    parcialidad.pagada_por_admin_id = None
    db.session.commit()
    log_evento('parcialidad_pago_revertido', nivel='warning',
               descripcion=f'Parcialidad #{parcialidad.numero} (plan {parcialidad.plan_id}) revertida a pendiente',
               administrador_id=admin_id)
    return parcialidad
