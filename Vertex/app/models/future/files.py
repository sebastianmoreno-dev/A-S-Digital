"""Archivos adjuntos reutilizables entre módulos (tickets, proyectos, cotizaciones).

Patrón polimórfico simple vía (entidad_tipo, entidad_id): no hay FK de
BD real sobre entidad_id porque puede apuntar a distintas tablas según
entidad_tipo. Es un trade-off deliberado y documentado (la integridad
referencial de esa relación se valida en la capa de aplicación) a
cambio de no tener una tabla de adjuntos por cada módulo.
"""
from app.extensions import db
from app.models.base import TimestampMixin


class ArchivoAdjunto(db.Model, TimestampMixin):
    __tablename__ = 'archivos_adjuntos'

    id = db.Column(db.Integer, primary_key=True)
    nombre_original = db.Column(db.String(255), nullable=False)
    nombre_almacenado = db.Column(db.String(255), nullable=False)
    ruta_o_url = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    tamano_bytes = db.Column(db.Integer, nullable=True)

    entidad_tipo = db.Column(db.String(40), nullable=False, index=True)  # 'contacto' | 'ticket' | 'proyecto' | ...
    entidad_id = db.Column(db.Integer, nullable=False, index=True)

    subido_por_admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True)

    subido_por = db.relationship('Administrador')
