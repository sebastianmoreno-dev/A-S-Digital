"""Orquesta el guardado de un lead válido: sanitiza, persiste, loguea y
dispara los correos (admin + confirmación al cliente) en background.

La detección de bots (honeypot / tiempo mínimo) NO vive aquí: se
resuelve en el blueprint antes de llamar a este servicio, porque la
respuesta a un bot detectado es "aparentar éxito sin guardar nada",
mientras que aquí siempre se persiste un contacto real.
"""
from flask import current_app

from app.extensions import db
from app.middlewares.request_logger import log_evento
from app.repositories import catalog_repository as catalog_repo
from app.repositories import lead_repository as lead_repo
from app.services import email_service
from app.utils import mailer
from app.utils.ip import get_client_ip
from app.validators.sanitizers import normalize_whitespace, strip_html


class ContactoInvalido(Exception):
    """El servicio o rango de presupuesto enviado no existe o no está activo."""


def registrar_contacto(app, *, nombre, empresa, email, telefono, servicio_id,
                        rango_presupuesto_id, descripcion_proyecto, user_agent):
    servicio = catalog_repo.obtener_servicio_activo(servicio_id)
    if servicio is None:
        raise ContactoInvalido('Selecciona un servicio válido.')

    rango = catalog_repo.obtener_rango_activo(rango_presupuesto_id) if rango_presupuesto_id else None

    try:
        contacto = lead_repo.crear_contacto(
            nombre=strip_html(normalize_whitespace(nombre))[:120],
            empresa=(strip_html(normalize_whitespace(empresa))[:120] or None) if empresa else None,
            email=strip_html(email).strip().lower()[:180],
            telefono=(strip_html(telefono).strip()[:30] or None) if telefono else None,
            servicio_id=servicio.id,
            rango_presupuesto_id=rango.id if rango else None,
            descripcion_proyecto=strip_html(descripcion_proyecto),
            ip=get_client_ip(),
            user_agent=(user_agent or '')[:255],
        )
    except Exception:
        db.session.rollback()
        log_evento('contacto_error', nivel='error', descripcion='Error guardando un contacto en BD')
        raise

    log_evento('contacto_exitoso', nivel='info', descripcion=f'Nuevo contacto #{contacto.id} — {contacto.email}')

    admin_destinatario, admin_asunto, admin_cuerpo = mailer.construir_correo_admin(
        contacto, current_app.config['ADMIN_EMAIL']
    )
    email_service.enviar_async(app, admin_destinatario, admin_asunto, admin_cuerpo, 'notificacion_admin', contacto.id)

    cli_destinatario, cli_asunto, cli_cuerpo = mailer.construir_correo_cliente(contacto)
    email_service.enviar_async(app, cli_destinatario, cli_asunto, cli_cuerpo, 'confirmacion_cliente', contacto.id)

    return contacto
