from app import db
from datetime import datetime


class Lead(db.Model):
    __tablename__ = 'leads'

    id          = db.Column(db.Integer,  primary_key=True)
    nombre      = db.Column(db.String(120), nullable=False)
    empresa     = db.Column(db.String(120), nullable=True)
    email       = db.Column(db.String(120), nullable=False)
    telefono    = db.Column(db.String(30),  nullable=True)
    servicio    = db.Column(db.String(50),  nullable=False)   # frontend | backend | fullstack | otro
    presupuesto = db.Column(db.String(50),  nullable=True)
    mensaje     = db.Column(db.Text,        nullable=False)
    creado_en   = db.Column(db.DateTime,    default=datetime.utcnow)
    leido       = db.Column(db.Boolean,     default=False)

    def __repr__(self):
        return f'<Lead {self.nombre} — {self.servicio}>'

    def to_dict(self):
        return {
            'id':          self.id,
            'nombre':      self.nombre,
            'empresa':     self.empresa,
            'email':       self.email,
            'telefono':    self.telefono,
            'servicio':    self.servicio,
            'presupuesto': self.presupuesto,
            'mensaje':     self.mensaje,
            'creado_en':   self.creado_en.strftime('%d/%m/%Y %H:%M'),
            'leido':       self.leido,
        }
