"""Lectura/escritura de la configuración operativa del sitio (tabla
configuracion_sitio) — así el equipo cambia teléfono, WhatsApp, redes
sociales u horarios sin tocar código.

Recordatorio: credenciales/API keys reales NO viven aquí, van en
variables de entorno (ver app/models/config.py para la justificación).
"""
from datetime import datetime

from app.extensions import db
from app.models.config import ConfiguracionSitio

_CONVERTERS = {
    'numero': lambda v: float(v) if v is not None else None,
    'booleano': lambda v: str(v).strip().lower() in ('1', 'true', 'yes', 'on') if v is not None else False,
    'texto': lambda v: v,
    'json': lambda v: v,
}


def obtener_valor(clave: str, default=None):
    fila = ConfiguracionSitio.query.filter_by(clave=clave).first()
    if not fila:
        return default
    convertir = _CONVERTERS.get(fila.tipo, lambda v: v)
    return convertir(fila.valor)


def listar_por_categoria(categoria: str | None = None):
    query = ConfiguracionSitio.query.order_by(ConfiguracionSitio.categoria, ConfiguracionSitio.clave)
    if categoria:
        query = query.filter_by(categoria=categoria)
    return query.all()


def listar_todo():
    return ConfiguracionSitio.query.order_by(ConfiguracionSitio.categoria, ConfiguracionSitio.clave).all()


def establecer_valor(clave: str, valor: str, admin_id: int | None = None) -> ConfiguracionSitio:
    fila = ConfiguracionSitio.query.filter_by(clave=clave).first()
    if not fila:
        raise ValueError(f'Clave de configuración desconocida: {clave}')
    fila.valor = valor
    fila.actualizado_en = datetime.utcnow()
    fila.actualizado_por_admin_id = admin_id
    db.session.commit()
    return fila
