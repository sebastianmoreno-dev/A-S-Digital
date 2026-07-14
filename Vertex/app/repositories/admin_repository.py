"""Acceso a datos de administradores, roles, sesiones e intentos de login."""
from datetime import datetime

from app.extensions import db
from app.models.admin import Administrador, IntentoLogin, Rol, SesionAdmin


def obtener_admin_por_email(email: str):
    return Administrador.query.filter_by(email=email.lower().strip()).first()


def obtener_admin(admin_id: int):
    return Administrador.query.get(admin_id)


def obtener_rol_por_nombre(nombre: str):
    return Rol.query.filter_by(nombre=nombre).first()


def registrar_intento_login(email: str, ip: str, user_agent: str, exitoso: bool, motivo_fallo: str | None = None):
    intento = IntentoLogin(
        email_intentado=email.lower().strip(),
        ip=ip,
        user_agent=user_agent,
        exitoso=exitoso,
        motivo_fallo=motivo_fallo,
    )
    db.session.add(intento)
    db.session.commit()
    return intento


def contar_intentos_fallidos_recientes(email: str, desde: datetime) -> int:
    return IntentoLogin.query.filter(
        IntentoLogin.email_intentado == email.lower().strip(),
        IntentoLogin.exitoso.is_(False),
        IntentoLogin.creado_en >= desde,
    ).count()


def crear_sesion_admin(administrador_id: int, token_hash: str, ip: str, user_agent: str, expira_en: datetime):
    sesion = SesionAdmin(
        administrador_id=administrador_id,
        token_hash=token_hash,
        ip=ip,
        user_agent=user_agent,
        expira_en=expira_en,
    )
    db.session.add(sesion)
    db.session.commit()
    return sesion


def listar_sesiones_activas(administrador_id: int):
    return SesionAdmin.query.filter_by(administrador_id=administrador_id, revocada=False).order_by(
        SesionAdmin.creado_en.desc()
    ).all()


def revocar_sesion(sesion_id: int, administrador_id: int) -> bool:
    sesion = SesionAdmin.query.filter_by(id=sesion_id, administrador_id=administrador_id).first()
    if not sesion:
        return False
    sesion.revocada = True
    db.session.commit()
    return True
