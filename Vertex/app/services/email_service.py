"""Envío de correo en un hilo de background (sin bloquear la respuesta HTTP)
con registro persistente en `correos_enviados` y un reintento simple.

Trade-off aceptado conscientemente: si el proceso muere antes de que el
hilo termine, ese correo se pierde (el lead en sí ya está a salvo en
BD). Para algo más robusto haría falta una cola real (Celery+Redis),
que quedó fuera de alcance por ahora.
"""
import threading
from datetime import datetime

from flask_mail import Message

from app.extensions import db, mail
from app.models.comms import CorreoEnviado

_MAX_INTENTOS = 2


def enviar_async(app, destinatario: str, asunto: str, cuerpo: str, tipo: str, contacto_id: int | None = None) -> None:
    """Dispara el envío en un hilo daemon. `app` debe ser la instancia real
    de Flask (current_app._get_current_object()) capturada en el hilo
    principal, porque el hilo nuevo no tiene contexto de aplicación."""
    hilo = threading.Thread(
        target=_enviar_y_registrar,
        args=(app, destinatario, asunto, cuerpo, tipo, contacto_id),
        daemon=True,
    )
    hilo.start()


def _enviar_y_registrar(app, destinatario, asunto, cuerpo, tipo, contacto_id) -> None:
    with app.app_context():
        registro = CorreoEnviado(
            destinatario=destinatario, asunto=asunto, tipo=tipo,
            contacto_id=contacto_id, estado='pendiente', intentos=0,
        )
        db.session.add(registro)
        db.session.commit()

        ultimo_error = None
        for _ in range(_MAX_INTENTOS):
            registro.intentos += 1
            try:
                mail.send(Message(subject=asunto, recipients=[destinatario], body=cuerpo))
                registro.estado = 'enviado'
                registro.enviado_en = datetime.utcnow()
                db.session.commit()
                return
            except Exception as exc:  # noqa: BLE001 - se registra cualquier fallo de envío
                ultimo_error = str(exc)[:2000]

        registro.estado = 'fallido'
        registro.error_detalle = ultimo_error
        db.session.commit()
