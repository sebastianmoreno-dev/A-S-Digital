"""Mensajes recibidos por el formulario de contacto/cotización."""
from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin


class Contacto(db.Model, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'contactos'

    ESTADOS = ('nuevo', 'en_seguimiento', 'cotizado', 'ganado', 'perdido', 'descartado')

    id = db.Column(db.Integer, primary_key=True)

    # ── Datos del formulario ────────────────────────────────────────
    nombre = db.Column(db.String(120), nullable=False)
    empresa = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(180), nullable=False, index=True)
    telefono = db.Column(db.String(30), nullable=True)

    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id', ondelete='RESTRICT'), nullable=False)
    rango_presupuesto_id = db.Column(
        db.Integer, db.ForeignKey('rangos_presupuesto.id', ondelete='SET NULL'), nullable=True
    )
    descripcion_proyecto = db.Column(db.Text, nullable=False)

    # ── Metadatos de la solicitud ────────────────────────────────────
    ip = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)

    # ── Gestión interna (CRM básico) ─────────────────────────────────
    estado = db.Column(db.Enum(*ESTADOS, name='contacto_estado'), default='nuevo', nullable=False, index=True)
    observaciones_internas = db.Column(db.Text, nullable=True)
    fecha_seguimiento = db.Column(db.Date, nullable=True)
    administrador_asignado_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True
    )

    servicio = db.relationship('Servicio', back_populates='contactos')
    rango_presupuesto = db.relationship('RangoPresupuesto', back_populates='contactos')
    administrador_asignado = db.relationship('Administrador')
    correos = db.relationship('CorreoEnviado', back_populates='contacto')

    def __repr__(self):
        return f'<Contacto {self.nombre} — {self.email}>'
