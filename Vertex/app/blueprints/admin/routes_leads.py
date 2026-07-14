from flask import abort, flash, redirect, render_template, request, url_for

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LeadForm
from app.decorators.auth import permission_required
from app.repositories import lead_repository as repo


@admin_bp.route('/leads')
@permission_required('leads.view')
def leads_list():
    estado = request.args.get('estado') or None
    page = request.args.get('page', 1, type=int)
    paginacion = repo.listar_contactos(estado=estado, page=page)
    return render_template('admin/leads_list.html', paginacion=paginacion, estado_filtro=estado)


@admin_bp.route('/leads/<int:lead_id>', methods=['GET', 'POST'])
@permission_required('leads.edit')
def lead_detail(lead_id):
    contacto = repo.obtener_contacto(lead_id)
    if contacto is None:
        abort(404)

    form = LeadForm(obj=contacto)
    if form.validate_on_submit():
        repo.actualizar_contacto(
            contacto,
            estado=form.estado.data,
            observaciones_internas=form.observaciones_internas.data,
            fecha_seguimiento=form.fecha_seguimiento.data,
        )
        flash('Lead actualizado.', 'success')
        return redirect(url_for('admin.lead_detail', lead_id=contacto.id))

    return render_template('admin/lead_detail.html', contacto=contacto, form=form)
