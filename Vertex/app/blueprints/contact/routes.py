from flask import Blueprint, current_app, flash, redirect, request, url_for

from app.blueprints.contact.forms import crear_formulario_contacto
from app.extensions import limiter
from app.middlewares.request_logger import log_evento
from app.services import contact_service
from app.services.contact_service import ContactoInvalido
from app.translations import t
from app.validators.contact_validators import is_honeypot_filled, is_submission_too_fast

contact_bp = Blueprint('contact', __name__)


def _limites_contacto() -> str:
    return current_app.config['CONTACT_RATE_LIMITS']


@contact_bp.route('/contacto/enviar', methods=['POST'])
@limiter.limit(_limites_contacto)
def enviar():
    form = crear_formulario_contacto()

    # ── Antibot: honeypot + tiempo mínimo — respuesta idéntica a un
    # envío exitoso para no darle pistas a quien lo dispara ───────────
    honeypot_disparado = is_honeypot_filled(form.website.data)
    envio_muy_rapido = is_submission_too_fast(form.form_ts.data, current_app.config['CONTACT_MIN_SECONDS'])

    if honeypot_disparado or envio_muy_rapido:
        motivo = 'honeypot' if honeypot_disparado else 'tiempo_minimo'
        log_evento('contacto_bot_detectado', nivel='warning', descripcion=f'Envío descartado ({motivo})')
        flash(t('flash.enviado'), 'success')
        return redirect(url_for('main.contacto'))

    if not form.validate_on_submit():
        for errores_campo in form.errors.values():
            for error in errores_campo:
                # str() resuelve los LazyT de los validadores; flash
                # serializa a sesión y necesita un str plano.
                flash(str(error), 'error')
        return redirect(url_for('main.contacto'))

    try:
        contact_service.registrar_contacto(
            current_app._get_current_object(),
            nombre=form.nombre.data,
            empresa=form.empresa.data,
            email=form.email.data,
            telefono=form.telefono.data,
            servicio_id=form.servicio_id.data,
            rango_presupuesto_id=form.rango_presupuesto_id.data or None,
            descripcion_proyecto=form.descripcion_proyecto.data,
            user_agent=request.headers.get('User-Agent', ''),
        )
    except ContactoInvalido as error:
        flash(str(error), 'error')
        return redirect(url_for('main.contacto'))
    except Exception:
        flash(t('flash.error_guardar'), 'error')
        return redirect(url_for('main.contacto'))

    flash(t('flash.enviado'), 'success')
    return redirect(url_for('main.contacto'))
