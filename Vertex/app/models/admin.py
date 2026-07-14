"""Staff interno: roles, permisos, administradores, sesiones y tokens.

No existe una tabla genérica de "usuarios": el sitio no tiene ni
tendrá registro público de clientes. Solo el equipo interno (staff)
se autentica, para leer y gestionar lo que entra por el formulario de
contacto y administrar el catálogo/config del sitio.
"""
from datetime import datetime

from flask_login import UserMixin

from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin

# ── Roles y permisos (N:M) ─────────────────────────────────────────

rol_permisos = db.Table(
    'rol_permisos',
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permiso_id', db.Integer, db.ForeignKey('permisos.id', ondelete='CASCADE'), primary_key=True),
)


class Rol(db.Model, TimestampMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)

    permisos = db.relationship('Permiso', secondary=rol_permisos, back_populates='roles', lazy='joined')
    administradores = db.relationship('Administrador', back_populates='rol')

    def tiene_permiso(self, clave: str) -> bool:
        return any(p.clave == clave for p in self.permisos)

    def __repr__(self):
        return f'<Rol {self.nombre}>'


class Permiso(db.Model):
    __tablename__ = 'permisos'

    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(80), unique=True, nullable=False)  # ej. 'leads.view'
    descripcion = db.Column(db.String(255), nullable=True)

    roles = db.relationship('Rol', secondary=rol_permisos, back_populates='permisos')

    def __repr__(self):
        return f'<Permiso {self.clave}>'


# ── Administradores (staff) ─────────────────────────────────────────

class Administrador(db.Model, UserMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
    rol = db.relationship('Rol', back_populates='administradores')

    activo = db.Column(db.Boolean, default=True, nullable=False)

    two_factor_secret = db.Column(db.String(64), nullable=True)
    two_factor_habilitado = db.Column(db.Boolean, default=False, nullable=False)

    ultimo_login_en = db.Column(db.DateTime, nullable=True)

    sesiones = db.relationship('SesionAdmin', back_populates='administrador', cascade='all, delete-orphan')

    # UserMixin usa get_id() -> str(self.id) por default, y is_active
    # se puede sobreescribir para respetar el flag `activo` (soft-delete).
    @property
    def is_active(self) -> bool:  # noqa: D401 - override de UserMixin
        return self.activo

    def tiene_permiso(self, clave: str) -> bool:
        return self.rol is not None and self.rol.tiene_permiso(clave)

    def __repr__(self):
        return f'<Administrador {self.email}>'


class SesionAdmin(db.Model, TimestampMixin):
    __tablename__ = 'sesiones_admin'

    id = db.Column(db.Integer, primary_key=True)
    administrador_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='CASCADE'), nullable=False, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    expira_en = db.Column(db.DateTime, nullable=False)
    revocada = db.Column(db.Boolean, default=False, nullable=False)

    administrador = db.relationship('Administrador', back_populates='sesiones')

    def esta_vigente(self) -> bool:
        return not self.revocada and self.expira_en > datetime.utcnow()

    def __repr__(self):
        return f'<SesionAdmin admin={self.administrador_id}>'


class IntentoLogin(db.Model, TimestampMixin):
    """Bitácora específica de intentos de login, para lockout por fuerza bruta."""
    __tablename__ = 'intentos_login'

    id = db.Column(db.Integer, primary_key=True)
    email_intentado = db.Column(db.String(180), nullable=False, index=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    exitoso = db.Column(db.Boolean, default=False, nullable=False)
    motivo_fallo = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<IntentoLogin {self.email_intentado} exitoso={self.exitoso}>'


class Token(db.Model, TimestampMixin):
    """Tokens de un solo uso: recuperación de contraseña, verificación de correo.

    El token CSRF de Flask-WTF NO se guarda aquí: vive firmado en la
    sesión/cookie del usuario y se valida en cada request sin tocar la
    base de datos.
    """
    __tablename__ = 'tokens'

    TIPO_PASSWORD_RESET = 'password_reset'
    TIPO_EMAIL_VERIFICATION = 'email_verification'
    TIPOS = (TIPO_PASSWORD_RESET, TIPO_EMAIL_VERIFICATION)

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum(*TIPOS, name='token_tipo'), nullable=False)
    administrador_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='CASCADE'), nullable=True, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expira_en = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)
    ip_solicitante = db.Column(db.String(45), nullable=True)

    administrador = db.relationship('Administrador')

    def esta_vigente(self) -> bool:
        return not self.usado and self.expira_en > datetime.utcnow()

    def __repr__(self):
        return f'<Token {self.tipo} admin={self.administrador_id}>'


class AdminBackupCode(db.Model, TimestampMixin):
    """Códigos de respaldo para 2FA. Esquema listo; el flujo 2FA aún no
    está activado en el panel (queda para una fase futura)."""
    __tablename__ = 'admin_2fa_codigos_respaldo'

    id = db.Column(db.Integer, primary_key=True)
    administrador_id = db.Column(
        db.Integer, db.ForeignKey('administradores.id', ondelete='CASCADE'), nullable=False, index=True
    )
    codigo_hash = db.Column(db.String(64), nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)

    administrador = db.relationship('Administrador')
