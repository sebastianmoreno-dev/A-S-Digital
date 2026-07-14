"""Mixins comunes para los modelos."""
from datetime import datetime

from app.extensions import db


class TimestampMixin:
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class UpdatedAtMixin:
    actualizado_en = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
