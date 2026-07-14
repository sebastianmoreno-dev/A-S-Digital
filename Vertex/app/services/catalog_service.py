"""Lógica de negocio del catálogo de servicios y rangos de presupuesto."""
from app.models.catalog import RangoPresupuesto, Servicio
from app.repositories import catalog_repository as repo


def servicios_para_formulario():
    return repo.listar_servicios_activos()


def rangos_para_formulario():
    return repo.listar_rangos_activos()


def crear_servicio(clave: str, nombre: str, descripcion: str, precio_desde, orden: int = 0) -> Servicio:
    servicio = Servicio(clave=clave, nombre=nombre, descripcion=descripcion, precio_desde=precio_desde, orden=orden)
    return repo.guardar_servicio(servicio)


def actualizar_servicio(servicio: Servicio, **campos) -> Servicio:
    for clave, valor in campos.items():
        setattr(servicio, clave, valor)
    return repo.guardar_servicio(servicio)


def crear_rango(clave: str, etiqueta: str, monto_min, monto_max, orden: int = 0) -> RangoPresupuesto:
    rango = RangoPresupuesto(clave=clave, etiqueta=etiqueta, monto_min=monto_min, monto_max=monto_max, orden=orden)
    return repo.guardar_rango(rango)


def actualizar_rango(rango: RangoPresupuesto, **campos) -> RangoPresupuesto:
    for clave, valor in campos.items():
        setattr(rango, clave, valor)
    return repo.guardar_rango(rango)
