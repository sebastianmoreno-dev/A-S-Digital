from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


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
