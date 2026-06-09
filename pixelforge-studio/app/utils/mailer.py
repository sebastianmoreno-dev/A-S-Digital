from flask_mail import Message
from app import mail
import os


def enviar_notificacion(lead):
    """
    Envía dos correos:
      1. Notificación al admin con los datos del lead.
      2. Confirmación automática al cliente.
    """
    admin_email = os.getenv('ADMIN_EMAIL', 'hola@pixelforgestudio.mx')

    # ── 1. Correo al admin ────────────────────────────────────────
    cuerpo_admin = f"""
Nuevo mensaje desde PixelForge Studio

Nombre:      {lead.nombre}
Empresa:     {lead.empresa or '—'}
Email:       {lead.email}
Teléfono:    {lead.telefono or '—'}
Servicio:    {lead.servicio}
Presupuesto: {lead.presupuesto or '—'}

Mensaje:
{lead.mensaje}

Recibido: {lead.creado_en.strftime('%d/%m/%Y %H:%M')} UTC
Lead ID:  #{lead.id}
""".strip()

    msg_admin = Message(
        subject    = f'[PixelForge] Nuevo lead: {lead.nombre} — {lead.servicio}',
        recipients = [admin_email],
        body       = cuerpo_admin,
    )
    mail.send(msg_admin)

    # ── 2. Confirmación al cliente ────────────────────────────────
    cuerpo_cliente = f"""
Hola {lead.nombre},

Gracias por contactarnos. Recibimos tu mensaje y te responderemos
en menos de 24 horas hábiles.

Resumen de tu solicitud:
  Servicio:    {lead.servicio}
  Presupuesto: {lead.presupuesto or 'Por definir'}

Si tienes algo más que agregar, responde este correo o escríbenos
por WhatsApp: https://wa.me/521234567890

— El equipo de PixelForge Studio
  hola@pixelforgestudio.mx
""".strip()

    msg_cliente = Message(
        subject    = 'Recibimos tu mensaje — PixelForge Studio',
        recipients = [lead.email],
        body       = cuerpo_cliente,
    )
    mail.send(msg_cliente)
