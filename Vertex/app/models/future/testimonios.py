"""Testimonios de clientes."""
from app.extensions import db
from app.models.base import TimestampMixin


class Testimonio(db.Model, TimestampMixin):
    __tablename__ = 'testimonios'

    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(120), nullable=False)
    empresa = db.Column(db.String(120), nullable=True)
    cargo = db.Column(db.String(120), nullable=True)
    contenido = db.Column(db.Text, nullable=False)
    calificacion = db.Column(db.Integer, nullable=True)
    foto_url = db.Column(db.String(255), nullable=True)
    aprobado = db.Column(db.Boolean, default=False, nullable=False, index=True)

    __table_args__ = (
        db.CheckConstraint('calificacion IS NULL OR (calificacion BETWEEN 1 AND 5)', name='ck_testimonio_calificacion'),
    )
