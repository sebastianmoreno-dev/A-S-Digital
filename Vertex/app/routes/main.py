from flask import Blueprint, render_template, abort, redirect, request, session, url_for

main_bp = Blueprint('main', __name__)

# ── Páginas principales ──────────────────────────────────────────

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/servicios')
def servicios():
    return render_template('servicios.html')

@main_bp.route('/portafolio')
def portafolio():
    return render_template('portafolio.html')

@main_bp.route('/proceso')
def proceso():
    return render_template('proceso.html')

@main_bp.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@main_bp.route('/contacto')
def contacto():
    return render_template('contacto.html')

# ── Páginas de detalle de cada servicio ─────────────────────────

# Mapa slug → template
SERVICIOS = {
    'landing-page': 'servicio_landing_page.html',
    'frontend':     'servicio_frontend.html',
    'backend':      'servicio_backend.html',
    'fullstack':    'servicio_fullstack.html',
    'blog-cms':     'servicio_blog_cms.html',
}

@main_bp.route('/servicios/<slug>')
def servicio_detalle(slug):
    template = SERVICIOS.get(slug)
    if not template:
        abort(404)
    return render_template(template)

# ── Páginas legales ──────────────────────────────────────────────

@main_bp.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')

@main_bp.route('/terminos')
def terminos():
    return render_template('terminos.html')

# ── Cambio de idioma ─────────────────────────────────────────────

@main_bp.route('/idioma/<lang>')
def cambiar_idioma(lang):
    if lang in ('es', 'en'):
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))

# ── 404 personalizado ────────────────────────────────────────────

@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404
