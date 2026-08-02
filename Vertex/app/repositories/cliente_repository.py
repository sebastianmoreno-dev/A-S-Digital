"""Acceso a datos de clientes y sus proyectos/sitios."""
from app.extensions import db
from app.models.future.crm import Cliente, ProyectoCliente


def crear_cliente(**campos) -> Cliente:
    cliente = Cliente(**campos)
    db.session.add(cliente)
    db.session.commit()
    return cliente


def obtener_cliente(cliente_id: int):
    return Cliente.query.get(cliente_id)


def listar_clientes():
    return Cliente.query.order_by(Cliente.creado_en.desc()).all()


def actualizar_cliente(cliente: Cliente, **campos) -> Cliente:
    for clave, valor in campos.items():
        setattr(cliente, clave, valor)
    db.session.commit()
    return cliente


def crear_proyecto(**campos) -> ProyectoCliente:
    proyecto = ProyectoCliente(**campos)
    db.session.add(proyecto)
    db.session.commit()
    return proyecto
