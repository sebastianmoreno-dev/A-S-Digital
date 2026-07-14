"""Chat en vivo (web / WhatsApp)."""
from datetime import datetime

from app.extensions import db


class ChatConversacion(db.Model):
    __tablename__ = 'chat_conversaciones'

    CANALES = ('web', 'whatsapp')

    id = db.Column(db.Integer, primary_key=True)
    contacto_id = db.Column(db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='SET NULL'), nullable=True)
    canal = db.Column(db.Enum(*CANALES, name='chat_canal'), default='web', nullable=False)
    iniciado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cerrado_en = db.Column(db.DateTime, nullable=True)

    contacto = db.relationship('Contacto')
    cliente = db.relationship('Cliente')
    mensajes = db.relationship('ChatMensaje', back_populates='conversacion', cascade='all, delete-orphan')


class ChatMensaje(db.Model):
    __tablename__ = 'chat_mensajes'

    REMITENTE_TIPOS = ('visitante', 'admin', 'bot')

    id = db.Column(db.Integer, primary_key=True)
    conversacion_id = db.Column(
        db.Integer, db.ForeignKey('chat_conversaciones.id', ondelete='CASCADE'), nullable=False, index=True
    )
    remitente_tipo = db.Column(db.Enum(*REMITENTE_TIPOS, name='chat_remitente_tipo'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    conversacion = db.relationship('ChatConversacion', back_populates='mensajes')
