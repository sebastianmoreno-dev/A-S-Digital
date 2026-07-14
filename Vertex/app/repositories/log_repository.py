"""Consultas de solo lectura sobre la bitácora, para el panel admin."""
from app.models.security import BitacoraEvento


def listar_eventos_recientes(limit: int = 100, tipo_evento: str | None = None, nivel: str | None = None):
    query = BitacoraEvento.query.order_by(BitacoraEvento.creado_en.desc())
    if tipo_evento:
        query = query.filter_by(tipo_evento=tipo_evento)
    if nivel:
        query = query.filter_by(nivel=nivel)
    return query.limit(limit).all()
