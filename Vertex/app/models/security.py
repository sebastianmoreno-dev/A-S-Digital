"""Bitácora de eventos, auditoría de rate limiting y lista negra de IPs."""
from datetime import datetime

from app.extensions import db
from app.models.base import TimestampMixin


class BitacoraEvento(db.Model):
    """Tabla única de eventos del sistema (envíos, errores, accesos,
    bloqueos, cambios administrativos). Se evita una tabla por módulo
    para no duplicar estructura y para poder auditar todo en un solo
    lugar ordenado por fecha."""
    __tablename__ = 'bitacora_eventos'

    NIVELES = ('info', 'warning', 'error', 'critical')

    id = db.Column(db.Integer, primary_key=True)
    tipo_evento = db.Column(db.String(60), nullable=False, index=True)
    nivel = db.Column(db.Enum(*NIVELES, name='bitacora_nivel'), default='info', nullable=False)

    administrador_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True
    )
    ip = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    extra = db.Column(db.JSON, nullable=True)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    administrador = db.relationship('Administrador')

    def __repr__(self):
        return f'<BitacoraEvento {self.tipo_evento} [{self.nivel}]>'


class RateLimitViolacion(db.Model, TimestampMixin):
    """Rastro de auditoría de límites excedidos.

    El conteo en tiempo real de solicitudes vive en Redis (Flask-Limiter);
    aquí solo se escribe cuando un límite se excede, para no generar una
    escritura en MySQL por cada request del sitio.
    """
    __tablename__ = 'rate_limit_violaciones'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    endpoint = db.Column(db.String(120), nullable=False)
    limite_excedido = db.Column(db.String(40), nullable=False)  # ej. '5 per minute'
    num_solicitudes = db.Column(db.Integer, nullable=False)
    ventana_inicio = db.Column(db.DateTime, nullable=False)
    ventana_fin = db.Column(db.DateTime, nullable=False)
    resulto_en_bloqueo = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<RateLimitViolacion {self.ip} {self.endpoint}>'


class ListaNegraIP(db.Model, TimestampMixin):
    __tablename__ = 'lista_negra_ip'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), unique=True, nullable=False, index=True)
    motivo = db.Column(db.String(255), nullable=False)
    bloqueado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bloqueo_permanente = db.Column(db.Boolean, default=False, nullable=False)
    expira_en = db.Column(db.DateTime, nullable=True)
    creado_por_admin_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True
    )
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)

    creado_por = db.relationship('Administrador')

    def esta_vigente(self) -> bool:
        if not self.activo:
            return False
        if self.bloqueo_permanente:
            return True
        return self.expira_en is None or self.expira_en > datetime.utcnow()

    def __repr__(self):
        return f'<ListaNegraIP {self.ip}>'
