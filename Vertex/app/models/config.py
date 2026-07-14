"""Configuración operativa del sitio, editable desde el panel admin.

Deliberadamente NO se guardan credenciales/API keys reales aquí (SMTP,
servicios externos, etc.) — esas viven en variables de entorno
(.env / secretos del servidor). Esta tabla es para datos públicos u
operativos que cambian seguido: correo de contacto, teléfono,
WhatsApp, redes sociales, horarios. Guardar secretos en una tabla
editable desde un panel web sería exponerlos a cualquiera con acceso
de escritura a esa pantalla, sin necesidad.
"""
from app.extensions import db


class ConfiguracionSitio(db.Model):
    __tablename__ = 'configuracion_sitio'

    TIPOS = ('texto', 'numero', 'booleano', 'json')

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(80), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.Enum(*TIPOS, name='config_tipo'), default='texto', nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(60), nullable=True, index=True)  # 'contacto', 'redes_sociales', 'horarios'...

    actualizado_en = db.Column(db.DateTime, nullable=True)
    actualizado_por_admin_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True
    )

    actualizado_por = db.relationship('Administrador')

    def __repr__(self):
        return f'<ConfiguracionSitio {self.clave}>'
