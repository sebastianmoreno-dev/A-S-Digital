"""Construcción del contenido de los correos del formulario de contacto.

Solo arma asunto/cuerpo a partir de un Contacto — el envío real y el
registro en `correos_enviados` viven en app.services.email_service.
"""
from app.models.contacto import Contacto


def construir_correo_admin(contacto: Contacto, admin_email: str) -> tuple[str, str, str]:
    presupuesto = contacto.rango_presupuesto.etiqueta if contacto.rango_presupuesto else '—'
    cuerpo = f"""
Nuevo mensaje de contacto — AS Vertex

Nombre:      {contacto.nombre}
Empresa:     {contacto.empresa or '—'}
Email:       {contacto.email}
Teléfono:    {contacto.telefono or '—'}
Servicio:    {contacto.servicio.nombre}
Presupuesto: {presupuesto}

Descripción del proyecto:
{contacto.descripcion_proyecto}

Recibido: {contacto.creado_en.strftime('%d/%m/%Y %H:%M')} UTC
IP: {contacto.ip}
Contacto ID: #{contacto.id}
""".strip()
    asunto = f'[AS Vertex] Nuevo lead: {contacto.nombre} — {contacto.servicio.nombre}'
    return admin_email, asunto, cuerpo


def construir_correo_cliente(contacto: Contacto) -> tuple[str, str, str]:
    presupuesto = contacto.rango_presupuesto.etiqueta if contacto.rango_presupuesto else 'Por definir'
    cuerpo = f"""
Hola {contacto.nombre},

Gracias por contactarnos. Recibimos tu solicitud y te responderemos
en menos de 24 horas hábiles.

Resumen de tu solicitud:
  Servicio:    {contacto.servicio.nombre}
  Presupuesto: {presupuesto}

— El equipo de AS Vertex
""".strip()
    asunto = 'Recibimos tu mensaje — AS Vertex'
    return contacto.email, asunto, cuerpo
