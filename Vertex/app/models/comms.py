"""Historial de correos enviados por el sistema."""
from app.extensions import db
from app.models.base import TimestampMixin


class CorreoEnviado(db.Model, TimestampMixin):
    __tablename__ = 'correos_enviados'

    TIPOS = ('notificacion_admin', 'confirmacion_cliente', 'password_reset', 'otro')
    ESTADOS = ('enviado', 'fallido', 'pendiente')

    id = db.Column(db.Integer, primary_key=True)
    destinatario = db.Column(db.String(180), nullable=False)
    asunto = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Enum(*TIPOS, name='correo_tipo'), nullable=False)

    contacto_id = db.Column(db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True)

    estado = db.Column(db.Enum(*ESTADOS, name='correo_estado'), default='pendiente', nullable=False, index=True)
    error_detalle = db.Column(db.Text, nullable=True)
    intentos = db.Column(db.Integer, default=0, nullable=False)
    enviado_en = db.Column(db.DateTime, nullable=True)

    contacto = db.relationship('Contacto', back_populates='correos')

    def __repr__(self):
        return f'<CorreoEnviado {self.destinatario} [{self.estado}]>'
