"""Empuja los precios/rangos actuales a una base de datos YA sembrada.

El `seed.py` es idempotente y solo INSERTA lo que falta: nunca actualiza
filas que ya existen. Por eso, tras bajar los precios en `seed.py`, la BD
de producción (Postgres en el homelab) se queda con los valores viejos.

Este script toma como fuente de verdad las listas SERVICIOS y RANGOS de
`seed.py` y hace UPDATE de las filas existentes que coincidan por `clave`:

  - Servicio        -> precio_desde
  - RangoPresupuesto -> etiqueta, monto_min, monto_max

No crea ni borra filas, no toca leads ni ninguna otra tabla, y es seguro
correrlo varias veces (idempotente). Las `clave` NO se modifican: son
identificadores internos que los leads ya guardados referencian.

Uso:
    python scripts/update_precios.py            # aplica los cambios
    python scripts/update_precios.py --dry-run  # solo muestra qué cambiaría

Carga el .env igual que seed.py, para apuntar a la misma DATABASE_URL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.catalog import RangoPresupuesto, Servicio  # noqa: E402
from scripts.seed import RANGOS, SERVICIOS  # noqa: E402


def _fmt(valor):
    return '—' if valor is None else str(valor)


def _actualizar_servicios(dry_run: bool) -> int:
    cambios = 0
    for datos in SERVICIOS:
        servicio = Servicio.query.filter_by(clave=datos['clave']).first()
        if not servicio:
            print(f"  · servicio '{datos['clave']}' no existe en la BD — se omite (usa seed.py para crearlo)")
            continue

        nuevo = datos.get('precio_desde')
        actual = None if servicio.precio_desde is None else float(servicio.precio_desde)
        objetivo = None if nuevo is None else float(nuevo)
        if actual == objetivo:
            continue

        print(f"  · {datos['clave']}: precio_desde {_fmt(actual)} -> {_fmt(objetivo)}")
        if not dry_run:
            servicio.precio_desde = nuevo
        cambios += 1
    return cambios


def _actualizar_rangos(dry_run: bool) -> int:
    cambios = 0
    for datos in RANGOS:
        rango = RangoPresupuesto.query.filter_by(clave=datos['clave']).first()
        if not rango:
            print(f"  · rango '{datos['clave']}' no existe en la BD — se omite (usa seed.py para crearlo)")
            continue

        def _num(v):
            return None if v is None else float(v)

        difs = []
        if rango.etiqueta != datos['etiqueta']:
            difs.append(f"etiqueta '{rango.etiqueta}' -> '{datos['etiqueta']}'")
        if _num(rango.monto_min) != _num(datos.get('monto_min')):
            difs.append(f"min {_fmt(_num(rango.monto_min))} -> {_fmt(_num(datos.get('monto_min')))}")
        if _num(rango.monto_max) != _num(datos.get('monto_max')):
            difs.append(f"max {_fmt(_num(rango.monto_max))} -> {_fmt(_num(datos.get('monto_max')))}")

        if not difs:
            continue

        print(f"  · {datos['clave']}: " + '; '.join(difs))
        if not dry_run:
            rango.etiqueta = datos['etiqueta']
            rango.monto_min = datos.get('monto_min')
            rango.monto_max = datos.get('monto_max')
        cambios += 1
    return cambios


def main():
    dry_run = '--dry-run' in sys.argv

    app = create_app()
    with app.app_context():
        print(f"BD objetivo: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print('Servicios:')
        n_serv = _actualizar_servicios(dry_run)
        print('Rangos de presupuesto:')
        n_rango = _actualizar_rangos(dry_run)

        total = n_serv + n_rango
        if dry_run:
            print(f"\n[dry-run] {total} fila(s) cambiarían. No se escribió nada.")
        elif total:
            db.session.commit()
            print(f"\nHecho: {total} fila(s) actualizada(s).")
        else:
            print('\nNada que actualizar: la BD ya coincide con seed.py.')


if __name__ == '__main__':
    main()
