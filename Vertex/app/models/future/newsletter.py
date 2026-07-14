"""Suscriptores al newsletter."""
from datetime import datetime

from app.extensions import db


class NewsletterSuscriptor(db.Model):
    __tablename__ = 'newsletter_suscriptores'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=True)
    confirmado = db.Column(db.Boolean, default=False, nullable=False)
    token_confirmacion = db.Column(db.String(64), nullable=True)
    suscrito_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    dado_de_baja_en = db.Column(db.DateTime, nullable=True)
