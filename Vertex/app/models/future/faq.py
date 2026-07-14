"""Preguntas frecuentes."""
from app.extensions import db


class PreguntaFrecuente(db.Model):
    __tablename__ = 'preguntas_frecuentes'

    id = db.Column(db.Integer, primary_key=True)
    pregunta = db.Column(db.String(255), nullable=False)
    respuesta = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(80), nullable=True)
    orden = db.Column(db.Integer, default=0, nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
