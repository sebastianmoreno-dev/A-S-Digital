"""Inicializa Flask-Limiter y conecta el rate limiting con la lista negra:

- Antes de cada request se rechaza cualquier IP en `lista_negra_ip` vigente.
- Cuando Flask-Limiter dispara un 429, se registra en
  `rate_limit_violaciones`; si una IP acumula demasiadas violaciones en
  la ventana configurada, se bloquea automáticamente insertándola en
  `lista_negra_ip` (bloqueo temporal, no permanente).
"""
from datetime import datetime, timedelta

from flask import current_app, jsonify, request

from app.extensions import db, limiter
from app.middlewares.request_logger import log_evento
from app.models.security import ListaNegraIP, RateLimitViolacion
from app.utils.ip import get_client_ip


def init_rate_limiting(app) -> None:
    limiter.init_app(app)

    @app.before_request
    def _rechazar_ip_en_lista_negra():
        if request.endpoint == 'static':
            return None

        ip = get_client_ip()
        bloqueo = ListaNegraIP.query.filter_by(ip=ip, activo=True).first()
        if bloqueo and bloqueo.esta_vigente():
            log_evento('acceso_bloqueado', nivel='warning', descripcion=f'IP en lista negra: {bloqueo.motivo}')
            return jsonify(error='Acceso denegado.'), 403
        return None

    @app.errorhandler(429)
    def _rate_limit_excedido(error):
        ip = get_client_ip()
        endpoint = request.endpoint or request.path
        limite = getattr(error, 'description', 'límite excedido')
        ahora = datetime.utcnow()

        violacion = RateLimitViolacion(
            ip=ip,
            endpoint=str(endpoint),
            limite_excedido=str(limite),
            num_solicitudes=0,
            ventana_inicio=ahora,
            ventana_fin=ahora,
        )
        db.session.add(violacion)
        db.session.commit()

        umbral = current_app.config['RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK']
        horas_bloqueo = current_app.config['RATE_LIMIT_BLOCK_HOURS']
        desde = ahora - timedelta(hours=horas_bloqueo)

        violaciones_recientes = RateLimitViolacion.query.filter(
            RateLimitViolacion.ip == ip, RateLimitViolacion.creado_en >= desde
        ).count()

        ya_bloqueada = ListaNegraIP.query.filter_by(ip=ip, activo=True).first()

        if violaciones_recientes >= umbral and not ya_bloqueada:
            db.session.add(ListaNegraIP(
                ip=ip,
                motivo=f'{violaciones_recientes} violaciones de rate limit en {horas_bloqueo}h',
                bloqueo_permanente=False,
                expira_en=ahora + timedelta(hours=horas_bloqueo),
            ))
            violacion.resulto_en_bloqueo = True
            db.session.commit()
            log_evento('bloqueo_ip', nivel='critical', descripcion=f'IP {ip} bloqueada automáticamente ({violaciones_recientes} violaciones)')
        else:
            log_evento('rate_limit_excedido', nivel='warning', descripcion=f'{endpoint} — {limite}')

        return jsonify(error='Demasiadas solicitudes. Intenta de nuevo más tarde.'), 429
