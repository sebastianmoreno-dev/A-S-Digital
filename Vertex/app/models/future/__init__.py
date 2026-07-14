"""Modelos de módulos futuros (blog, portafolio, CRM, tickets, chat, etc.).

Se crean ahora junto con el resto del esquema para no necesitar
migraciones destructivas más adelante, pero todavía no tienen
blueprints/rutas/plantillas — eso se construye cuando el módulo
correspondiente entre en desarrollo.
"""
from app.models.future.blog import BlogCategoria, BlogPost
from app.models.future.crm import Cliente, Cotizacion, ProyectoCliente, ReunionAgenda
from app.models.future.faq import PreguntaFrecuente
from app.models.future.files import ArchivoAdjunto
from app.models.future.newsletter import NewsletterSuscriptor
from app.models.future.portfolio import PortafolioImagen, PortafolioProyecto
from app.models.future.testimonios import Testimonio
from app.models.future.tickets import TicketMensaje, TicketSoporte
from app.models.future.chat import ChatConversacion, ChatMensaje

__all__ = [
    'BlogCategoria', 'BlogPost',
    'Cliente', 'Cotizacion', 'ProyectoCliente', 'ReunionAgenda',
    'PreguntaFrecuente',
    'ArchivoAdjunto',
    'NewsletterSuscriptor',
    'PortafolioImagen', 'PortafolioProyecto',
    'Testimonio',
    'TicketMensaje', 'TicketSoporte',
    'ChatConversacion', 'ChatMensaje',
]
