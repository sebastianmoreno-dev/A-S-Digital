"""Decorador de autorización para el panel admin (RBAC)."""
from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def permission_required(clave: str):
    """Exige sesión activa (Flask-Login) y que el rol del admin tenga
    el permiso indicado (ver app.models.admin.Permiso)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.tiene_permiso(clave):
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
