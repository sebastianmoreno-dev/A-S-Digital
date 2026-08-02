"""Lógica de negocio de clientes: alta manual y conversión desde un lead ganado."""
from app.middlewares.request_logger import log_evento
from app.models.contacto import Contacto
from app.repositories import cliente_repository as repo


def crear_cliente(*, nombre, empresa=None, email=None, telefono=None, notas=None,
                  creado_desde_contacto_id=None, admin_id=None):
    cliente = repo.crear_cliente(
        nombre=nombre, empresa=empresa, email=email, telefono=telefono, notas=notas,
        creado_desde_contacto_id=creado_desde_contacto_id,
    )
    log_evento('cliente_creado', nivel='info',
               descripcion=f'Cliente #{cliente.id} — {cliente.nombre}',
               administrador_id=admin_id)
    return cliente


def convertir_lead(contacto: Contacto, *, admin_id=None):
    """Crea un Cliente a partir de un lead ganado y un primer proyecto/sitio
    ligado a ese lead. Reutiliza los datos del contacto."""
    cliente = repo.crear_cliente(
        nombre=contacto.nombre,
        empresa=contacto.empresa,
        email=contacto.email,
        telefono=contacto.telefono,
        creado_desde_contacto_id=contacto.id,
    )
    repo.crear_proyecto(
        cliente_id=cliente.id,
        contacto_id=contacto.id,
        nombre=f'{contacto.servicio.nombre} — {contacto.nombre}',
        descripcion=contacto.descripcion_proyecto,
        estado='propuesta',
    )
    log_evento('cliente_creado', nivel='info',
               descripcion=f'Cliente #{cliente.id} convertido desde lead #{contacto.id}',
               administrador_id=admin_id)
    return cliente
