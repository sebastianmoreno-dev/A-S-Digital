"""Portafolio de proyectos realizados."""
from app.extensions import db
from app.models.base import TimestampMixin


class PortafolioProyecto(db.Model, TimestampMixin):
    __tablename__ = 'portafolio_proyectos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    cliente = db.Column(db.String(160), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    imagen_portada = db.Column(db.String(255), nullable=True)
    tecnologias = db.Column(db.String(255), nullable=True)
    destacado = db.Column(db.Boolean, default=False, nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)
    publicado = db.Column(db.Boolean, default=False, nullable=False, index=True)

    imagenes = db.relationship('PortafolioImagen', back_populates='proyecto', cascade='all, delete-orphan')


class PortafolioImagen(db.Model):
    __tablename__ = 'portafolio_imagenes'

    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('portafolio_proyectos.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)
    alt_text = db.Column(db.String(180), nullable=True)

    proyecto = db.relationship('PortafolioProyecto', back_populates='imagenes')
