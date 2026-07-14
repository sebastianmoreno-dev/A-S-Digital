from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.blueprints.admin import admin_bp
from app.decorators.auth import permission_required
from app.services import config_service


@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@permission_required('config.manage')
def configuracion():
    if request.method == 'POST':
        for fila in config_service.listar_todo():
            nuevo_valor = request.form.get(f'valor_{fila.id}')
            if nuevo_valor is not None and nuevo_valor != (fila.valor or ''):
                config_service.establecer_valor(fila.clave, nuevo_valor, admin_id=current_user.id)
        flash('Configuración actualizada.', 'success')
        return redirect(url_for('admin.configuracion'))

    return render_template('admin/config.html', filas=config_service.listar_todo())
