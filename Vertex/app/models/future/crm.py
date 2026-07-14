"""CRM básico: clientes, proyectos, cotizaciones y agenda de reuniones."""
from app.extensions import db
from app.models.base import TimestampMixin


class Cliente(db.Model, TimestampMixin):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    empresa = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(180), nullable=True, index=True)
    telefono = db.Column(db.String(30), nullable=True)
    notas = db.Column(db.Text, nullable=True)

    # Un cliente casi siempre nace de un lead convertido
    creado_desde_contacto_id = db.Column(
        db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True
    )

    contacto_origen = db.relationship('Contacto')
    proyectos = db.relationship('ProyectoCliente', back_populates='cliente')
    cotizaciones = db.relationship('Cotizacion', back_populates='cliente')
    reuniones = db.relationship('ReunionAgenda', back_populates='cliente')


class ProyectoCliente(db.Model, TimestampMixin):
    __tablename__ = 'proyectos_cliente'

    ESTADOS = ('propuesta', 'en_progreso', 'completado', 'cancelado')

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False, index=True)
    nombre = db.Column(db.String(160), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.Enum(*ESTADOS, name='proyecto_estado'), default='propuesta', nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin_estimada = db.Column(db.Date, nullable=True)
    fecha_fin_real = db.Column(db.Date, nullable=True)
    monto_acordado = db.Column(db.Numeric(10, 2), nullable=True)

    cliente = db.relationship('Cliente', back_populates='proyectos')


class Cotizacion(db.Model, TimestampMixin):
    __tablename__ = 'cotizaciones'

    ESTADOS = ('borrador', 'enviada', 'aceptada', 'rechazada', 'expirada')

    id = db.Column(db.Integer, primary_key=True)
    contacto_id = db.Column(db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='SET NULL'), nullable=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id', ondelete='RESTRICT'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    moneda = db.Column(db.String(3), default='MXN', nullable=False)
    estado = db.Column(db.Enum(*ESTADOS, name='cotizacion_estado'), default='borrador', nullable=False, index=True)
    valida_hasta = db.Column(db.Date, nullable=True)
    pdf_url = db.Column(db.String(255), nullable=True)
    creado_por_admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True)

    contacto = db.relationship('Contacto')
    cliente = db.relationship('Cliente', back_populates='cotizaciones')
    servicio = db.relationship('Servicio')
    creado_por = db.relationship('Administrador')


class ReunionAgenda(db.Model, TimestampMixin):
    __tablename__ = 'reuniones_agenda'

    ESTADOS = ('programada', 'confirmada', 'cancelada', 'completada')

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='SET NULL'), nullable=True)
    contacto_id = db.Column(db.Integer, db.ForeignKey('contactos.id', ondelete='SET NULL'), nullable=True)
    administrador_id = db.Column(db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True)
    titulo = db.Column(db.String(160), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=True)
    ubicacion_o_link = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.Enum(*ESTADOS, name='reunion_estado'), default='programada', nullable=False)

    cliente = db.relationship('Cliente', back_populates='reuniones')
    contacto = db.relationship('Contacto')
    administrador = db.relationship('Administrador')
