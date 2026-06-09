from flask import Blueprint, request, redirect, url_for, flash, render_template
from app import db
from app.models.lead import Lead
from app.utils.mailer import enviar_notificacion
import os

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/contacto/enviar', methods=['POST'])
def enviar():
    # ── Recoger datos del formulario ──────────────────────────────
    nombre      = request.form.get('nombre',      '').strip()
    empresa     = request.form.get('empresa',     '').strip()
    email       = request.form.get('email',       '').strip()
    telefono    = request.form.get('telefono',    '').strip()
    servicio    = request.form.get('servicio',    '').strip()
    presupuesto = request.form.get('presupuesto', '').strip()
    mensaje     = request.form.get('mensaje',     '').strip()

    # ── Validación básica ─────────────────────────────────────────
    errores = []
    if not nombre:
        errores.append('El nombre es requerido.')
    if not email or '@' not in email:
        errores.append('Ingresa un correo válido.')
    if not servicio:
        errores.append('Selecciona un servicio.')
    if not mensaje:
        errores.append('El mensaje no puede estar vacío.')

    if errores:
        for err in errores:
            flash(err, 'error')
        return redirect(url_for('main.contacto'))

    # ── Guardar lead en la base de datos ──────────────────────────
    try:
        lead = Lead(
            nombre      = nombre,
            empresa     = empresa,
            email       = email,
            telefono    = telefono,
            servicio    = servicio,
            presupuesto = presupuesto,
            mensaje     = mensaje,
        )
        db.session.add(lead)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Hubo un problema guardando tu mensaje. Intenta de nuevo.', 'error')
        return redirect(url_for('main.contacto'))

    # ── Enviar notificación por correo ────────────────────────────
    try:
        enviar_notificacion(lead)
    except Exception:
        # El correo falla silenciosamente — el lead ya está guardado
        pass

    flash('¡Mensaje enviado! Te respondemos en menos de 24 horas.', 'success')
    return redirect(url_for('main.contacto'))
