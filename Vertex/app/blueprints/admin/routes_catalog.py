from flask import abort, flash, redirect, render_template, url_for

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import RangoPresupuestoForm, ServicioForm
from app.decorators.auth import permission_required
from app.repositories import catalog_repository as repo
from app.services import catalog_service

# ── Servicios ──────────────────────────────────────────────────────

@admin_bp.route('/servicios')
@permission_required('catalogo.manage')
def servicios_list():
    return render_template('admin/servicios_list.html', servicios=repo.listar_todos_servicios())


@admin_bp.route('/servicios/nuevo', methods=['GET', 'POST'])
@permission_required('catalogo.manage')
def servicio_nuevo():
    form = ServicioForm()
    if form.validate_on_submit():
        catalog_service.crear_servicio(
            clave=form.clave.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio_desde=form.precio_desde.data,
            orden=form.orden.data or 0,
        )
        flash('Servicio creado.', 'success')
        return redirect(url_for('admin.servicios_list'))
    return render_template('admin/servicio_form.html', form=form, titulo='Nuevo servicio')


@admin_bp.route('/servicios/<int:servicio_id>/editar', methods=['GET', 'POST'])
@permission_required('catalogo.manage')
def servicio_editar(servicio_id):
    servicio = repo.obtener_servicio(servicio_id)
    if servicio is None:
        abort(404)

    form = ServicioForm(obj=servicio)
    if form.validate_on_submit():
        catalog_service.actualizar_servicio(
            servicio,
            clave=form.clave.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio_desde=form.precio_desde.data,
            orden=form.orden.data or 0,
            activo=form.activo.data,
        )
        flash('Servicio actualizado.', 'success')
        return redirect(url_for('admin.servicios_list'))
    return render_template('admin/servicio_form.html', form=form, titulo='Editar servicio')


# ── Rangos de presupuesto ────────────────────────────────────────────

@admin_bp.route('/presupuestos')
@permission_required('catalogo.manage')
def rangos_list():
    return render_template('admin/rangos_list.html', rangos=repo.listar_todos_rangos())


@admin_bp.route('/presupuestos/nuevo', methods=['GET', 'POST'])
@permission_required('catalogo.manage')
def rango_nuevo():
    form = RangoPresupuestoForm()
    if form.validate_on_submit():
        catalog_service.crear_rango(
            clave=form.clave.data,
            etiqueta=form.etiqueta.data,
            monto_min=form.monto_min.data,
            monto_max=form.monto_max.data,
            orden=form.orden.data or 0,
        )
        flash('Rango creado.', 'success')
        return redirect(url_for('admin.rangos_list'))
    return render_template('admin/rango_form.html', form=form, titulo='Nuevo rango de presupuesto')


@admin_bp.route('/presupuestos/<int:rango_id>/editar', methods=['GET', 'POST'])
@permission_required('catalogo.manage')
def rango_editar(rango_id):
    rango = repo.obtener_rango(rango_id)
    if rango is None:
        abort(404)

    form = RangoPresupuestoForm(obj=rango)
    if form.validate_on_submit():
        catalog_service.actualizar_rango(
            rango,
            clave=form.clave.data,
            etiqueta=form.etiqueta.data,
            monto_min=form.monto_min.data,
            monto_max=form.monto_max.data,
            orden=form.orden.data or 0,
            activo=form.activo.data,
        )
        flash('Rango actualizado.', 'success')
        return redirect(url_for('admin.rangos_list'))
    return render_template('admin/rango_form.html', form=form, titulo='Editar rango de presupuesto')
