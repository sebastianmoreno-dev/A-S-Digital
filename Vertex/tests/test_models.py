from datetime import datetime, timedelta

from app.models.admin import Permiso, Rol
from app.models.security import ListaNegraIP


def test_rol_tiene_permiso(app, db):
    with app.app_context():
        rol = Rol(nombre='Editor')
        permiso = Permiso(clave='leads.view')
        db.session.add_all([rol, permiso])
        db.session.flush()
        rol.permisos = [permiso]
        db.session.commit()

        assert rol.tiene_permiso('leads.view') is True
        assert rol.tiene_permiso('config.manage') is False


def test_lista_negra_bloqueo_temporal_expira(app, db):
    with app.app_context():
        vigente = ListaNegraIP(ip='1.1.1.1', motivo='test', bloqueo_permanente=False,
                                expira_en=datetime.utcnow() + timedelta(hours=1))
        expirado = ListaNegraIP(ip='2.2.2.2', motivo='test', bloqueo_permanente=False,
                                 expira_en=datetime.utcnow() - timedelta(hours=1))
        permanente = ListaNegraIP(ip='3.3.3.3', motivo='test', bloqueo_permanente=True, expira_en=None)
        db.session.add_all([vigente, expirado, permanente])
        db.session.commit()

        assert vigente.esta_vigente() is True
        assert expirado.esta_vigente() is False
        assert permanente.esta_vigente() is True
