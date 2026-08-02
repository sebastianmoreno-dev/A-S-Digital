"""Consultas de solo lectura sobre la bitácora, para el panel admin."""
from app.models.security import BitacoraEvento

# Categorías de eventos para el Dashboard. Separan lo operativo del negocio
# de lo de seguridad/sistema (logins, IPs, bloqueos), que no debe ser lo
# primero que se ve ni exponerse si se comparte pantalla con alguien externo.
EVENTOS_NEGOCIO = ('contacto_exitoso', 'lead_creado_manual', 'lead_estado_cambiado')
EVENTOS_SEGURIDAD = (
    'login', 'logout', 'login_fallido', 'login_bloqueado',
    'acceso_bloqueado', 'bloqueo_ip', 'rate_limit_excedido',
    'contacto_bot_detectado', 'contacto_error',
)


def listar_eventos_recientes(limit: int = 100, categoria: str | None = None,
                            tipo_evento: str | None = None, nivel: str | None = None,
                            desde=None, hasta=None):
    """Lista eventos, con filtros opcionales.

    - categoria: 'negocio' | 'seguridad' — filtra por el conjunto de tipos.
    - nivel: info | warning | error | critical.
    - desde / hasta: objetos date (rango sobre creado_en, inclusivo).
    """
    query = BitacoraEvento.query.order_by(BitacoraEvento.creado_en.desc())

    if categoria == 'negocio':
        query = query.filter(BitacoraEvento.tipo_evento.in_(EVENTOS_NEGOCIO))
    elif categoria == 'seguridad':
        query = query.filter(BitacoraEvento.tipo_evento.in_(EVENTOS_SEGURIDAD))

    if tipo_evento:
        query = query.filter_by(tipo_evento=tipo_evento)
    if nivel:
        query = query.filter_by(nivel=nivel)
    if desde is not None:
        query = query.filter(BitacoraEvento.creado_en >= desde)
    if hasta is not None:
        # 'hasta' es un date; incluir todo ese día hasta el final.
        from datetime import datetime, time
        query = query.filter(BitacoraEvento.creado_en <= datetime.combine(hasta, time.max))

    return query.limit(limit).all()
