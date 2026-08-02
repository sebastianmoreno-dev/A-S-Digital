"""Planes de pago a nivel Cliente y sus parcialidades.

Un cliente tiene un plan (monto total, frecuencia, fecha de inicio) del que
se derivan N parcialidades con fecha de vencimiento y monto. El registro de
"pagada" es manual (no hay pasarela): lo marca quien administra el panel.
"""
from datetime import date

from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin


class PlanPago(db.Model, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'planes_pago'

    # Frecuencias soportadas por el modelo. Hoy se implementa el cálculo de
    # 'quincenal_15_fin' (vencimientos fijos los días 15 y último de cada mes);
    # las demás quedan modeladas para agregarlas sin rehacer el esquema.
    FRECUENCIAS = ('quincenal_15_fin', 'mensual', 'semanal', 'personalizada')

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer, db.ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    moneda = db.Column(db.String(3), default='MXN', nullable=False)
    frecuencia = db.Column(
        db.Enum(*FRECUENCIAS, name='plan_frecuencia'),
        default='quincenal_15_fin', nullable=False,
    )
    fecha_inicio = db.Column(db.Date, nullable=False)  # = 1ª fecha de vencimiento
    num_parcialidades = db.Column(db.Integer, nullable=False)
    notas = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    cliente = db.relationship('Cliente', backref=db.backref('planes_pago', cascade='all, delete-orphan'))
    parcialidades = db.relationship(
        'Parcialidad', back_populates='plan',
        cascade='all, delete-orphan', order_by='Parcialidad.numero',
    )

    def __repr__(self):
        return f'<PlanPago cliente={self.cliente_id} ${self.monto_total}>'


class Parcialidad(db.Model, TimestampMixin):
    __tablename__ = 'parcialidades'

    ESTADOS = ('pendiente', 'pagada')

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(
        db.Integer, db.ForeignKey('planes_pago.id', ondelete='CASCADE'), nullable=False, index=True
    )
    numero = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False, index=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.Enum(*ESTADOS, name='parcialidad_estado'), default='pendiente', nullable=False, index=True)
    fecha_pago = db.Column(db.Date, nullable=True)
    pagada_por_admin_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True
    )

    plan = db.relationship('PlanPago', back_populates='parcialidades')
    pagada_por = db.relationship('Administrador')

    @property
    def esta_vencida(self) -> bool:
        """Vencida = pendiente y con fecha de vencimiento ya pasada.
        Se calcula, no se almacena, para que se actualice sola con el tiempo."""
        return self.estado != 'pagada' and self.fecha_vencimiento < date.today()

    @property
    def estado_visible(self) -> str:
        """Estado para la UI: 'pagada' | 'vencida' | 'pendiente'."""
        if self.estado == 'pagada':
            return 'pagada'
        return 'vencida' if self.esta_vencida else 'pendiente'

    def __repr__(self):
        return f'<Parcialidad #{self.numero} {self.fecha_vencimiento} {self.estado}>'
