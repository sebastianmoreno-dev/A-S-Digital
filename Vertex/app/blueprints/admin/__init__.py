from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../templates/admin')

# Los módulos de rutas se registran importándolos al final, para que
# decoren este mismo blueprint (evita imports circulares con forms.py).
from app.blueprints.admin import (  # noqa: E402,F401
    routes_auth, routes_catalog, routes_clientes, routes_config, routes_leads,
)
