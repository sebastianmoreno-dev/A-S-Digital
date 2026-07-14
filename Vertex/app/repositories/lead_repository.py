"""Acceso a datos de los leads (contactos) del formulario."""
from app.extensions import db
from app.models.contacto import Contacto


def crear_contacto(**campos) -> Contacto:
    contacto = Contacto(**campos)
    db.session.add(contacto)
    db.session.commit()
    return contacto


def obtener_contacto(contacto_id: int):
    return Contacto.query.get(contacto_id)


def listar_contactos(estado: str | None = None, page: int = 1, per_page: int = 25):
    query = Contacto.query.order_by(Contacto.creado_en.desc())
    if estado:
        query = query.filter_by(estado=estado)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def actualizar_contacto(contacto: Contacto, **campos) -> Contacto:
    for clave, valor in campos.items():
        setattr(contacto, clave, valor)
    db.session.commit()
    return contacto
