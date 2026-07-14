"""Acceso a datos de la lista negra de IPs."""
from datetime import datetime, timedelta

from app.extensions import db
from app.models.security import ListaNegraIP


def obtener_bloqueo_activo(ip: str):
    return ListaNegraIP.query.filter_by(ip=ip, activo=True).first()


def esta_bloqueada(ip: str) -> bool:
    bloqueo = obtener_bloqueo_activo(ip)
    return bool(bloqueo and bloqueo.esta_vigente())


def bloquear_ip(ip: str, motivo: str, permanente: bool = False, horas: int | None = None, admin_id: int | None = None):
    expira_en = None if permanente or not horas else datetime.utcnow() + timedelta(hours=horas)
    bloqueo = ListaNegraIP(
        ip=ip,
        motivo=motivo,
        bloqueo_permanente=permanente,
        expira_en=expira_en,
        creado_por_admin_id=admin_id,
    )
    db.session.add(bloqueo)
    db.session.commit()
    return bloqueo


def desbloquear_ip(ip: str) -> bool:
    bloqueo = obtener_bloqueo_activo(ip)
    if not bloqueo:
        return False
    bloqueo.activo = False
    db.session.commit()
    return True


def listar_bloqueos_activos():
    return ListaNegraIP.query.filter_by(activo=True).order_by(ListaNegraIP.bloqueado_en.desc()).all()
