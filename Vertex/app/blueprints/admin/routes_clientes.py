from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import ClienteForm, PlanPagoForm, ProyectoForm
from app.decorators.auth import permission_required
from app.repositories import cliente_repository as repo
from app.repositories import lead_repository as lead_repo
from app.repositories import pago_repository as pago_repo
from app.services import cliente_service, pagos_service


@admin_bp.route('/clientes')
@permission_required('clientes.manage')
def clientes_list():
    clientes = repo.listar_clientes()
    # Resumen financiero por cliente para la columna de estado.
    resumenes = {}
    for c in clientes:
        plan = pago_repo.plan_activo_de_cliente(c.id)
        resumenes[c.id] = pagos_service.resumen_financiero(plan) if plan else None
    return render_template('admin/clientes_list.html', clientes=clientes, resumenes=resumenes)


@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@permission_required('clientes.manage')
def cliente_nuevo():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = cliente_service.crear_cliente(
            nombre=form.nombre.data.strip(),
            empresa=(form.empresa.data or '').strip() or None,
            email=(form.email.data or '').strip().lower() or None,
            telefono=(form.telefono.data or '').strip() or None,
            notas=(form.notas.data or '').strip() or None,
            admin_id=current_user.id,
        )
        if form.proyecto_nombre.data:
            repo.crear_proyecto(cliente_id=cliente.id, nombre=form.proyecto_nombre.data.strip(),
                                estado='propuesta')
        flash('Cliente creado.', 'success')
        return redirect(url_for('admin.cliente_detail', cliente_id=cliente.id))
    return render_template('admin/cliente_form.html', form=form, titulo='Nuevo cliente')


@admin_bp.route('/leads/<int:lead_id>/convertir', methods=['POST'])
@permission_required('clientes.manage')
def cliente_desde_lead(lead_id):
    contacto = lead_repo.obtener_contacto(lead_id)
    if contacto is None:
        abort(404)
    cliente = cliente_service.convertir_lead(contacto, admin_id=current_user.id)
    flash('Lead convertido a cliente.', 'success')
    return redirect(url_for('admin.cliente_detail', cliente_id=cliente.id))


@admin_bp.route('/clientes/<int:cliente_id>')
@permission_required('clientes.manage')
def cliente_detail(cliente_id):
    cliente = repo.obtener_cliente(cliente_id)
    if cliente is None:
        abort(404)
    plan = pago_repo.plan_activo_de_cliente(cliente_id)
    resumen = pagos_service.resumen_financiero(plan) if plan else None
    return render_template('admin/cliente_detail.html', cliente=cliente, plan=plan,
                           resumen=resumen, hoy=date.today())


@admin_bp.route('/clientes/<int:cliente_id>/proyectos/nuevo', methods=['GET', 'POST'])
@permission_required('clientes.manage')
def proyecto_nuevo(cliente_id):
    cliente = repo.obtener_cliente(cliente_id)
    if cliente is None:
        abort(404)
    form = ProyectoForm()
    if form.validate_on_submit():
        repo.crear_proyecto(
            cliente_id=cliente.id, nombre=form.nombre.data.strip(),
            descripcion=(form.descripcion.data or '').strip() or None,
            monto_acordado=form.monto_acordado.data, estado='propuesta',
        )
        flash('Proyecto agregado.', 'success')
        return redirect(url_for('admin.cliente_detail', cliente_id=cliente.id))
    return render_template('admin/cliente_form.html', form=form, titulo='Nuevo proyecto / sitio',
                           es_proyecto=True, cliente=cliente)


@admin_bp.route('/clientes/<int:cliente_id>/plan', methods=['GET', 'POST'])
@permission_required('clientes.manage')
def cliente_plan(cliente_id):
    cliente = repo.obtener_cliente(cliente_id)
    if cliente is None:
        abort(404)
    plan = pago_repo.plan_activo_de_cliente(cliente_id)

    form = PlanPagoForm()
    if request.method == 'GET' and plan is not None:
        form.monto_total.data = plan.monto_total
        form.frecuencia.data = plan.frecuencia
        form.fecha_inicio.data = plan.fecha_inicio
        form.num_parcialidades.data = plan.num_parcialidades
        form.notas.data = plan.notas

    if form.validate_on_submit():
        # No se permite regenerar un plan que ya tiene pagos registrados.
        if plan is not None and pagos_service.hay_pagos_registrados(plan):
            flash('Este plan ya tiene pagos registrados; no se puede regenerar. '
                  'Marca/edita las parcialidades individualmente.', 'error')
            return redirect(url_for('admin.cliente_detail', cliente_id=cliente.id))

        try:
            # Resuelve el nº de parcialidades: explícito o derivado de la fecha de fin.
            num = form.num_parcialidades.data
            if not num:
                num = pagos_service.contar_vencimientos(
                    form.frecuencia.data, form.fecha_inicio.data, form.fecha_fin.data)
            if num < 1:
                flash('El rango de fechas no genera ninguna parcialidad.', 'error')
                return render_template('admin/plan_form.html', form=form, cliente=cliente, plan=plan)

            datos = dict(
                monto_total=form.monto_total.data, frecuencia=form.frecuencia.data,
                fecha_inicio=form.fecha_inicio.data, num_parcialidades=num,
                notas=(form.notas.data or '').strip() or None, admin_id=current_user.id,
            )
            if plan is None:
                pagos_service.crear_plan(cliente.id, **datos)
                flash(f'Plan de pagos creado ({num} parcialidades).', 'success')
            else:
                pagos_service.regenerar_plan(plan, **datos)
                flash(f'Plan de pagos actualizado ({num} parcialidades).', 'success')
            return redirect(url_for('admin.cliente_detail', cliente_id=cliente.id))
        except pagos_service.PlanInvalido as e:
            flash(str(e), 'error')

    return render_template('admin/plan_form.html', form=form, cliente=cliente, plan=plan)


@admin_bp.route('/parcialidades/<int:parcialidad_id>/pagar', methods=['POST'])
@permission_required('clientes.manage')
def parcialidad_pagar(parcialidad_id):
    parcialidad = pago_repo.obtener_parcialidad(parcialidad_id)
    if parcialidad is None:
        abort(404)
    fecha = request.form.get('fecha_pago')
    fecha_pago = None
    if fecha:
        try:
            fecha_pago = date.fromisoformat(fecha)
        except ValueError:
            fecha_pago = None
    pagos_service.marcar_pagada(parcialidad, fecha_pago=fecha_pago, admin_id=current_user.id)
    flash(f'Parcialidad #{parcialidad.numero} marcada como pagada.', 'success')
    return redirect(url_for('admin.cliente_detail', cliente_id=parcialidad.plan.cliente_id))


@admin_bp.route('/parcialidades/<int:parcialidad_id>/revertir', methods=['POST'])
@permission_required('clientes.manage')
def parcialidad_revertir(parcialidad_id):
    parcialidad = pago_repo.obtener_parcialidad(parcialidad_id)
    if parcialidad is None:
        abort(404)
    pagos_service.desmarcar_pagada(parcialidad, admin_id=current_user.id)
    flash(f'Parcialidad #{parcialidad.numero} revertida a pendiente.', 'success')
    return redirect(url_for('admin.cliente_detail', cliente_id=parcialidad.plan.cliente_id))
