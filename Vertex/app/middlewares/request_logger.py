"""Bitácora de eventos — un único punto para registrar lo que pasa en el sitio."""
from flask import request

from app.extensions import db
from app.models.security import BitacoraEvento
from app.utils.ip import get_client_ip


def log_evento(tipo_evento: str, nivel: str = 'info', descripcion: str | None = None,
                administrador_id: int | None = None, extra: dict | None = None) -> None:
    """Registra un evento en la bitácora. Nunca debe tumbar el flujo
    principal: si falla el logging, se ignora silenciosamente (el dato
    de negocio ya se guardó o se está por guardar; perder un log no
    debe romper la respuesta al usuario)."""
    try:
        evento = BitacoraEvento(
            tipo_evento=tipo_evento,
            nivel=nivel,
            administrador_id=administrador_id,
            ip=get_client_ip(),
            user_agent=request.headers.get('User-Agent', '')[:255],
            descripcion=descripcion,
            extra=extra,
        )
        db.session.add(evento)
        db.session.commit()
    except Exception:
        db.session.rollback()
