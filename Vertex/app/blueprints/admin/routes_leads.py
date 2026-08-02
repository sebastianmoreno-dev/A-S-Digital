from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LeadCrearForm, LeadForm
from app.decorators.auth import permission_required
from app.middlewares.request_logger import log_evento
from app.models.contacto import Contacto
from app.repositories import catalog_repository as catalog_repo
from app.repositories import lead_repository as repo
from app.utils.ip import get_client_ip


@admin_bp.route('/leads')
@permission_required('leads.view')
def leads_list():
    estado = request.args.get('estado') or None
    origen = request.args.get('origen') or None
    page = request.args.get('page', 1, type=int)
    paginacion = repo.listar_contactos(estado=estado, origen=origen, page=page)
    return render_template(
        'admin/leads_list.html',
        paginacion=paginacion,
        estado_filtro=estado,
        origen_filtro=origen,
        origenes=Contacto.ORIGENES,
    )


@admin_bp.route('/leads/nuevo', methods=['GET', 'POST'])
@permission_required('leads.edit')
def lead_nuevo():
    form = LeadCrearForm()
    # Selects poblados con el catálogo activo (mismos que ve el formulario público).
    form.servicio_id.choices = [(s.id, s.nombre) for s in catalog_repo.listar_servicios_activos()]
    form.rango_presupuesto_id.choices = [(0, '— Sin especificar —')] + [
        (r.id, r.etiqueta) for r in catalog_repo.listar_rangos_activos()
    ]

    if form.validate_on_submit():
        rango_id = form.rango_presupuesto_id.data or None
        contacto = repo.crear_contacto(
            nombre=form.nombre.data.strip()[:120],
            email=form.email.data.strip().lower()[:180],
            telefono=(form.telefono.data.strip()[:30] or None) if form.telefono.data else None,
            servicio_id=form.servicio_id.data,
            rango_presupuesto_id=rango_id if rango_id else None,
            # La nota libre alimenta la descripción del proyecto (campo obligatorio
            # del modelo). Si viene vacía se guarda un marcador claro.
            descripcion_proyecto=(form.nota.data or '').strip() or '(Lead capturado manualmente — sin descripción)',
            origen=form.origen.data,
            estado=form.estado.data,
            ip=get_client_ip(),
            user_agent=(request.headers.get('User-Agent', '') or '')[:255],
        )
        log_evento(
            'lead_creado_manual', nivel='info',
            descripcion=f'Lead manual #{contacto.id} — {contacto.email} (origen: {contacto.origen})',
            administrador_id=current_user.id,
        )
        flash('Lead registrado.', 'success')
        return redirect(url_for('admin.lead_detail', lead_id=contacto.id))

    return render_template('admin/lead_form.html', form=form, titulo='Nuevo lead')


@admin_bp.route('/leads/<int:lead_id>', methods=['GET', 'POST'])
@permission_required('leads.edit')
def lead_detail(lead_id):
    contacto = repo.obtener_contacto(lead_id)
    if contacto is None:
        abort(404)

    form = LeadForm(obj=contacto)
    if form.validate_on_submit():
        estado_anterior = contacto.estado
        repo.actualizar_contacto(
            contacto,
            estado=form.estado.data,
            observaciones_internas=form.observaciones_internas.data,
            fecha_seguimiento=form.fecha_seguimiento.data,
        )
        # Evento de negocio: cambio de estado del lead (para la vista Negocio del Dashboard).
        if form.estado.data != estado_anterior:
            log_evento(
                'lead_estado_cambiado', nivel='info',
                descripcion=f'Lead #{contacto.id}: {estado_anterior} → {contacto.estado}',
                administrador_id=current_user.id,
            )
        flash('Lead actualizado.', 'success')
        return redirect(url_for('admin.lead_detail', lead_id=contacto.id))

    return render_template('admin/lead_detail.html', contacto=contacto, form=form)
