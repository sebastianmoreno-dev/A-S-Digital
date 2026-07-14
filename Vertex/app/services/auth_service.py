"""Login/logout del panel admin: verificación de credenciales, bloqueo
por fuerza bruta (intentos_login) y registro de sesión (sesiones_admin)
además de la sesión de Flask-Login."""
from datetime import datetime, timedelta

from flask import current_app, request
from flask_login import login_user, logout_user

from app.middlewares.request_logger import log_evento
from app.repositories import admin_repository as repo
from app.utils.ip import get_client_ip
from app.utils.security import generate_secure_token, hash_token, verify_password


class LoginError(Exception):
    """Credenciales inválidas o cuenta bloqueada temporalmente."""


def intentar_login(email: str, password: str):
    email = (email or '').strip().lower()
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')[:255]

    max_intentos = current_app.config['LOGIN_MAX_ATTEMPTS']
    minutos_bloqueo = current_app.config['LOGIN_LOCKOUT_MINUTES']
    desde = datetime.utcnow() - timedelta(minutes=minutos_bloqueo)

    if repo.contar_intentos_fallidos_recientes(email, desde) >= max_intentos:
        repo.registrar_intento_login(email, ip, user_agent, exitoso=False, motivo_fallo='cuenta_bloqueada_temporalmente')
        log_evento('login_bloqueado', nivel='warning', descripcion=f'Cuenta bloqueada temporalmente: {email}')
        raise LoginError(f'Demasiados intentos fallidos. Intenta de nuevo en {minutos_bloqueo} minutos.')

    admin = repo.obtener_admin_por_email(email)
    credenciales_validas = admin is not None and admin.activo and verify_password(admin.password_hash, password)

    if not credenciales_validas:
        motivo = 'credenciales_invalidas' if admin else 'usuario_no_existe'
        repo.registrar_intento_login(email, ip, user_agent, exitoso=False, motivo_fallo=motivo)
        log_evento('login_fallido', nivel='warning', descripcion=f'Login fallido: {email}')
        raise LoginError('Correo o contraseña incorrectos.')

    repo.registrar_intento_login(email, ip, user_agent, exitoso=True)

    admin.ultimo_login_en = datetime.utcnow()
    token = generate_secure_token()
    repo.crear_sesion_admin(
        administrador_id=admin.id,
        token_hash=hash_token(token),
        ip=ip,
        user_agent=user_agent,
        expira_en=datetime.utcnow() + timedelta(days=7),
    )

    login_user(admin)
    log_evento('login', nivel='info', descripcion=f'Login exitoso: {email}', administrador_id=admin.id)
    return admin


def cerrar_sesion(administrador_id: int | None) -> None:
    logout_user()
    log_evento('logout', nivel='info', administrador_id=administrador_id)
