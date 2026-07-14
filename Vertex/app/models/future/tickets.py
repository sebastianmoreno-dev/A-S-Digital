"""Sistema de tickets de soporte."""
from datetime import datetime

from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin


class TicketSoporte(db.Model, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'tickets_soporte'

    ESTADOS = ('abierto', 'en_progreso', 'resuelto', 'cerrado')
    PRIORIDADES = ('baja', 'media', 'alta', 'urgente')

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='SET NULL'), nullable=True)
    contacto_id = db.Column(db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True)
    asunto = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.Enum(*ESTADOS, name='ticket_estado'), default='abierto', nullable=False, index=True)
    prioridad = db.Column(db.Enum(*PRIORIDADES, name='ticket_prioridad'), default='media', nullable=False)
    asignado_admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True)

    cliente = db.relationship('Cliente')
    contacto = db.relationship('Contacto')
    asignado = db.relationship('Administrador')
    mensajes = db.relationship('TicketMensaje', back_populates='ticket', cascade='all, delete-orphan')


class TicketMensaje(db.Model):
    __tablename__ = 'ticket_mensajes'

    AUTOR_TIPOS = ('cliente', 'admin')

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets_soporte.id', ondelete='CASCADE'), nullable=False, index=True)
    autor_tipo = db.Column(db.Enum(*AUTOR_TIPOS, name='ticket_autor_tipo'), nullable=False)
    autor_id = db.Column(db.Integer, nullable=True)  # id de Cliente o Administrador según autor_tipo
    mensaje = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ticket = db.relationship('TicketSoporte', back_populates='mensajes')
