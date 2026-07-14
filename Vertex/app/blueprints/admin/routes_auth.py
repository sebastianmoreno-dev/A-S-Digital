from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm
from app.models.contacto import Contacto
from app.repositories import log_repository
from app.services.auth_service import LoginError, cerrar_sesion, intentar_login


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            intentar_login(form.email.data, form.password.data)
            return redirect(url_for('admin.dashboard'))
        except LoginError as error:
            flash(str(error), 'error')

    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    cerrar_sesion(current_user.id)
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    conteos = {estado: Contacto.query.filter_by(estado=estado).count() for estado in Contacto.ESTADOS}
    ultimos_leads = Contacto.query.order_by(Contacto.creado_en.desc()).limit(8).all()
    eventos_recientes = log_repository.listar_eventos_recientes(limit=15)
    return render_template(
        'admin/dashboard.html',
        conteos=conteos,
        ultimos_leads=ultimos_leads,
        eventos_recientes=eventos_recientes,
    )
