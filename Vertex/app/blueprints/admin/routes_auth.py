from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm
from app.models.contacto import Contacto
from app.models.security import BitacoraEvento
from app.repositories import log_repository, pago_repository
from app.services.auth_service import LoginError, cerrar_sesion, intentar_login


def _parse_fecha(valor):
    """Convierte 'YYYY-MM-DD' a date; devuelve None si es inválida o vacía."""
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


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

    # Eventos: por defecto se muestran los de NEGOCIO. La pestaña de seguridad
    # (logins, IPs, bloqueos) queda aparte para no ser lo primero que se ve.
    categoria = request.args.get('cat', 'negocio')
    if categoria not in ('negocio', 'seguridad'):
        categoria = 'negocio'
    nivel = request.args.get('nivel') or None
    desde = _parse_fecha(request.args.get('desde'))
    hasta = _parse_fecha(request.args.get('hasta'))

    eventos_recientes = log_repository.listar_eventos_recientes(
        limit=20, categoria=categoria, nivel=nivel, desde=desde, hasta=hasta,
    )

    # Widget de pagos: vencidas y próximas parcialidades.
    pagos_vencidos = pago_repository.parcialidades_vencidas()
    pagos_proximos = pago_repository.proximas_parcialidades(limite=5)

    return render_template(
        'admin/dashboard.html',
        conteos=conteos,
        ultimos_leads=ultimos_leads,
        eventos_recientes=eventos_recientes,
        pagos_vencidos=pagos_vencidos,
        pagos_proximos=pagos_proximos,
        evento_categoria=categoria,
        evento_nivel=nivel,
        evento_desde=request.args.get('desde', ''),
        evento_hasta=request.args.get('hasta', ''),
        niveles=BitacoraEvento.NIVELES,
    )
