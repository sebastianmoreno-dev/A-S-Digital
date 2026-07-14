"""Importa todos los modelos para que Alembic (Flask-Migrate) los descubra
al generar migraciones, y para tener un único punto de import cómodo."""
from app.models.admin import (
    AdminBackupCode,
    Administrador,
    IntentoLogin,
    Permiso,
    Rol,
    SesionAdmin,
    Token,
    rol_permisos,
)
from app.models.catalog import RangoPresupuesto, Servicio
from app.models.comms import CorreoEnviado
from app.models.config import ConfiguracionSitio
from app.models.contacto import Contacto
from app.models.security import BitacoraEvento, ListaNegraIP, RateLimitViolacion
from app.models.future import (  # noqa: F401 - registra los modelos futuros en el metadata
    BlogCategoria,
    BlogPost,
    ChatConversacion,
    ChatMensaje,
    Cliente,
    Cotizacion,
    ArchivoAdjunto,
    NewsletterSuscriptor,
    PortafolioImagen,
    PortafolioProyecto,
    PreguntaFrecuente,
    ProyectoCliente,
    ReunionAgenda,
    Testimonio,
    TicketMensaje,
    TicketSoporte,
)

__all__ = [
    'AdminBackupCode', 'Administrador', 'IntentoLogin', 'Permiso', 'Rol', 'SesionAdmin', 'Token', 'rol_permisos',
    'RangoPresupuesto', 'Servicio',
    'CorreoEnviado',
    'ConfiguracionSitio',
    'Contacto',
    'BitacoraEvento', 'ListaNegraIP', 'RateLimitViolacion',
    'BlogCategoria', 'BlogPost', 'ChatConversacion', 'ChatMensaje', 'Cliente', 'Cotizacion',
    'ArchivoAdjunto', 'NewsletterSuscriptor', 'PortafolioImagen', 'PortafolioProyecto',
    'PreguntaFrecuente', 'ProyectoCliente', 'ReunionAgenda', 'Testimonio', 'TicketMensaje', 'TicketSoporte',
]
