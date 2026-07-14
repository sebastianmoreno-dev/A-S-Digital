"""Catálogo administrable desde el panel — nada de esto va hardcodeado en HTML."""
from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin


class Servicio(db.Model, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'servicios'

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(60), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio_desde = db.Column(db.Numeric(10, 2), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    orden = db.Column(db.Integer, default=0, nullable=False)

    contactos = db.relationship('Contacto', back_populates='servicio')

    def __repr__(self):
        return f'<Servicio {self.clave}>'


class RangoPresupuesto(db.Model, TimestampMixin):
    __tablename__ = 'rangos_presupuesto'

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(60), unique=True, nullable=False)
    etiqueta = db.Column(db.String(120), nullable=False)
    monto_min = db.Column(db.Numeric(10, 2), nullable=True)
    monto_max = db.Column(db.Numeric(10, 2), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    orden = db.Column(db.Integer, default=0, nullable=False)

    contactos = db.relationship('Contacto', back_populates='rango_presupuesto')

    def __repr__(self):
        return f'<RangoPresupuesto {self.clave}>'
