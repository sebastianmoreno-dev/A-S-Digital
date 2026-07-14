"""Seed inicial de la base de datos: roles, permisos, catálogo de
servicios/presupuestos, configuración del sitio y el primer administrador.

Uso:
    ADMIN_SEED_EMAIL=tu@correo.com ADMIN_SEED_PASSWORD='una-clave-fuerte' \
    python scripts/seed.py

Es idempotente: se puede correr varias veces sin duplicar datos.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.admin import Administrador, Permiso, Rol  # noqa: E402
from app.models.catalog import RangoPresupuesto, Servicio  # noqa: E402
from app.models.config import ConfiguracionSitio  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

PERMISOS = [
    ('leads.view', 'Ver leads del formulario de contacto'),
    ('leads.edit', 'Editar estado/notas de un lead'),
    ('catalogo.manage', 'Administrar servicios y rangos de presupuesto'),
    ('config.manage', 'Administrar la configuración operativa del sitio'),
    ('admins.manage', 'Administrar cuentas de administradores (futuro)'),
]

SERVICIOS = [
    dict(clave='landing-page', nombre='Landing Page', precio_desde=3500, orden=1,
         descripcion='Página única enfocada en conversión: presentación, servicios y contacto.'),
    dict(clave='frontend', nombre='Solo Frontend', precio_desde=5500, orden=2,
         descripcion='Diseño e implementación de interfaz — HTML, CSS y JavaScript.'),
    dict(clave='backend', nombre='Solo Backend / API', precio_desde=7500, orden=3,
         descripcion='API y lógica de servidor con Flask/Python y base de datos.'),
    dict(clave='fullstack', nombre='Sitio Completo (Full Stack)', precio_desde=14000, orden=4,
         descripcion='Frontend + backend + base de datos, listo para producción.'),
    dict(clave='blog-cms', nombre='Blog / CMS', precio_desde=9000, orden=5,
         descripcion='Sitio con panel para publicar contenido sin tocar código.'),
    dict(clave='otro', nombre='Otro / No sé aún', precio_desde=None, orden=6,
         descripcion='El cliente todavía no tiene claro qué necesita.'),
]

RANGOS = [
    dict(clave='menos5k', etiqueta='Menos de $5,000 MXN', monto_min=0, monto_max=5000, orden=1),
    dict(clave='5k-10k', etiqueta='$5,000 – $10,000 MXN', monto_min=5000, monto_max=10000, orden=2),
    dict(clave='10k-20k', etiqueta='$10,000 – $20,000 MXN', monto_min=10000, monto_max=20000, orden=3),
    dict(clave='mas20k', etiqueta='Más de $20,000 MXN', monto_min=20000, monto_max=None, orden=4),
]

CONFIGURACION = [
    dict(clave='contacto.email', valor='contacto.asvertex@gmail.com', categoria='contacto', descripcion='Correo de contacto público'),
    dict(clave='contacto.telefono', valor='', categoria='contacto', descripcion='Teléfono de contacto'),
    dict(clave='contacto.whatsapp', valor='', categoria='contacto', descripcion='Número de WhatsApp (con código de país)'),
    dict(clave='redes.github', valor='https://github.com/ASVertex', categoria='redes_sociales', descripcion='URL de GitHub'),
    dict(clave='redes.linkedin', valor='', categoria='redes_sociales', descripcion='URL de LinkedIn'),
    dict(clave='redes.instagram', valor='', categoria='redes_sociales', descripcion='URL de Instagram'),
    dict(clave='horario.texto', valor='Lun – Vie: 9:00 – 19:00 CST', categoria='horarios', descripcion='Horario de atención (texto libre)'),
]


def seed_permisos():
    for clave, descripcion in PERMISOS:
        if not Permiso.query.filter_by(clave=clave).first():
            db.session.add(Permiso(clave=clave, descripcion=descripcion))
    db.session.commit()


def seed_rol_administrador() -> Rol:
    rol = Rol.query.filter_by(nombre='Administrador').first()
    if not rol:
        rol = Rol(nombre='Administrador', descripcion='Acceso total al panel')
        db.session.add(rol)
        db.session.commit()
    rol.permisos = Permiso.query.all()
    db.session.commit()
    return rol


def seed_servicios():
    for datos in SERVICIOS:
        if not Servicio.query.filter_by(clave=datos['clave']).first():
            db.session.add(Servicio(**datos))
    db.session.commit()


def seed_rangos():
    for datos in RANGOS:
        if not RangoPresupuesto.query.filter_by(clave=datos['clave']).first():
            db.session.add(RangoPresupuesto(**datos))
    db.session.commit()


def seed_configuracion():
    for datos in CONFIGURACION:
        if not ConfiguracionSitio.query.filter_by(clave=datos['clave']).first():
            db.session.add(ConfiguracionSitio(**datos))
    db.session.commit()


def seed_admin_inicial(rol: Rol):
    email = os.getenv('ADMIN_SEED_EMAIL')
    password = os.getenv('ADMIN_SEED_PASSWORD')

    if not email or not password:
        print('ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD no definidos — se omite la creación del admin inicial.')
        return

    if Administrador.query.filter_by(email=email.lower().strip()).first():
        print(f'Ya existe un administrador con el correo {email}, no se crea de nuevo.')
        return

    admin = Administrador(
        nombre=os.getenv('ADMIN_SEED_NOMBRE', 'Administrador'),
        email=email.lower().strip(),
        password_hash=hash_password(password),
        rol_id=rol.id,
        activo=True,
    )
    db.session.add(admin)
    db.session.commit()
    print(f'Administrador inicial creado: {email}')


def main():
    app = create_app()
    with app.app_context():
        seed_permisos()
        rol_admin = seed_rol_administrador()
        seed_servicios()
        seed_rangos()
        seed_configuracion()
        seed_admin_inicial(rol_admin)
    print('Seed completado.')


if __name__ == '__main__':
    main()
