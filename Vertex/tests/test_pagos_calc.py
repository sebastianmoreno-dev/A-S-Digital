"""Fase 2 — cálculos de plan de pagos (dinero real, sin BD).

El caso real: parcialidades quincenales con vencimientos los días 15 y último
de cada mes, empezando el 31 de agosto de 2026, a un año (24 parcialidades).
"""
from datetime import date
from decimal import Decimal

import pytest

from app.services import pagos_service as svc


def test_caso_real_31ago2026_genera_24_fechas_exactas():
    fechas = svc.generar_vencimientos('quincenal_15_fin', date(2026, 8, 31), 24)
    esperado = [
        date(2026, 8, 31), date(2026, 9, 15), date(2026, 9, 30), date(2026, 10, 15),
        date(2026, 10, 31), date(2026, 11, 15), date(2026, 11, 30), date(2026, 12, 15),
        date(2026, 12, 31), date(2027, 1, 15), date(2027, 1, 31), date(2027, 2, 15),
        date(2027, 2, 28), date(2027, 3, 15), date(2027, 3, 31), date(2027, 4, 15),
        date(2027, 4, 30), date(2027, 5, 15), date(2027, 5, 31), date(2027, 6, 15),
        date(2027, 6, 30), date(2027, 7, 15), date(2027, 7, 31), date(2027, 8, 15),
    ]
    assert fechas == esperado


def test_alterna_15_y_ultimo_dia_por_mes():
    # Empezando en un día 15, la siguiente es el último del mismo mes.
    fechas = svc.generar_vencimientos('quincenal_15_fin', date(2026, 1, 15), 4)
    assert fechas == [date(2026, 1, 15), date(2026, 1, 31), date(2026, 2, 15), date(2026, 2, 28)]


def test_febrero_bisiesto_usa_29():
    fechas = svc.generar_vencimientos('quincenal_15_fin', date(2028, 2, 15), 2)
    assert fechas == [date(2028, 2, 15), date(2028, 2, 29)]  # 2028 bisiesto


def test_meses_de_30_dias():
    fechas = svc.generar_vencimientos('quincenal_15_fin', date(2026, 4, 15), 2)
    assert fechas == [date(2026, 4, 15), date(2026, 4, 30)]


def test_normaliza_inicio_no_ancla():
    # Un inicio que no es 15 ni fin de mes se ajusta a la ancla del mismo mes.
    assert svc.generar_vencimientos('quincenal_15_fin', date(2026, 8, 10), 1) == [date(2026, 8, 15)]
    assert svc.generar_vencimientos('quincenal_15_fin', date(2026, 8, 20), 1) == [date(2026, 8, 31)]


def test_contar_vencimientos_inicio_fin():
    # Del 31-ago-2026 al 15-ago-2027 hay 24 anclas (el caso real).
    assert svc.contar_vencimientos('quincenal_15_fin', date(2026, 8, 31), date(2027, 8, 15)) == 24
    assert svc.contar_vencimientos('quincenal_15_fin', date(2026, 8, 31), date(2026, 9, 15)) == 2
    assert svc.contar_vencimientos('quincenal_15_fin', date(2026, 9, 15), date(2026, 8, 1)) == 0


def test_frecuencia_no_soportada_lanza():
    with pytest.raises(svc.PlanInvalido):
        svc.generar_vencimientos('mensual', date(2026, 8, 31), 3)


@pytest.mark.parametrize('total,num', [
    ('12000.00', 24), ('10000.00', 24), ('9999.99', 7), ('100.00', 3), ('1.00', 3), ('50000', 13),
])
def test_partir_monto_suma_exacta(total, num):
    montos = svc.partir_monto(total, num)
    assert len(montos) == num
    assert sum(montos) == Decimal(str(total)).quantize(Decimal('0.01'))
    # Ninguna parcialidad difiere de otra en más de un centavo.
    assert max(montos) - min(montos) <= Decimal('0.01')


def test_partir_monto_reparte_sobrante_en_las_primeras():
    # 100.00 / 3 = 33.34, 33.33, 33.33  (suma 100.00)
    montos = svc.partir_monto('100.00', 3)
    assert montos == [Decimal('33.34'), Decimal('33.33'), Decimal('33.33')]
