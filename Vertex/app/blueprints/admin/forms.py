from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, DateField, DecimalField, IntegerField, PasswordField,
    SelectField, StringField, TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

from app.models.contacto import Contacto


class LoginForm(FlaskForm):
    email = StringField('Correo', validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField('Contraseña', validators=[DataRequired()])


def _origen_label(clave: str) -> str:
    return {
        'formulario_web': 'Formulario web',
        'referido': 'Referido',
        'redes_sociales': 'Redes sociales',
        'contacto_directo': 'Contacto directo',
        'otro': 'Otro',
    }.get(clave, clave.replace('_', ' ').title())


class LeadForm(FlaskForm):
    estado = SelectField('Estado', choices=[(e, e.replace('_', ' ').title()) for e in Contacto.ESTADOS])
    observaciones_internas = TextAreaField('Observaciones internas', validators=[Optional(), Length(max=4000)])
    fecha_seguimiento = DateField('Fecha de seguimiento', validators=[Optional()])


class LeadCrearForm(FlaskForm):
    """Alta manual de un lead conseguido fuera del formulario web
    (referido, redes, contacto directo, etc.)."""
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=180)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=30)])
    servicio_id = SelectField('Servicio de interés', coerce=int, validators=[DataRequired()])
    rango_presupuesto_id = SelectField('Rango de presupuesto', coerce=int, validators=[Optional()])
    origen = SelectField(
        'Origen',
        choices=[(o, _origen_label(o)) for o in Contacto.ORIGENES if o != 'formulario_web'],
        default='referido',
    )
    estado = SelectField(
        'Estado inicial',
        choices=[(e, e.replace('_', ' ').title()) for e in Contacto.ESTADOS],
        default='nuevo',
    )
    nota = TextAreaField('Nota', validators=[Optional(), Length(max=4000)])


class ServicioForm(FlaskForm):
    clave = StringField('Clave', validators=[DataRequired(), Length(max=60)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=2000)])
    precio_desde = DecimalField('Precio desde (MXN)', validators=[Optional(), NumberRange(min=0)], places=2)
    orden = IntegerField('Orden', validators=[Optional()], default=0)
    activo = BooleanField('Activo', default=True)


class RangoPresupuestoForm(FlaskForm):
    clave = StringField('Clave', validators=[DataRequired(), Length(max=60)])
    etiqueta = StringField('Etiqueta', validators=[DataRequired(), Length(max=120)])
    monto_min = DecimalField('Monto mínimo', validators=[Optional(), NumberRange(min=0)], places=2)
    monto_max = DecimalField('Monto máximo', validators=[Optional(), NumberRange(min=0)], places=2)
    orden = IntegerField('Orden', validators=[Optional()], default=0)
    activo = BooleanField('Activo', default=True)


class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    empresa = StringField('Empresa', validators=[Optional(), Length(max=120)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=180)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=30)])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=4000)])
    # Alta manual: opcionalmente crea un primer proyecto/sitio.
    proyecto_nombre = StringField('Primer proyecto / sitio (opcional)', validators=[Optional(), Length(max=160)])


class ProyectoForm(FlaskForm):
    nombre = StringField('Nombre del proyecto / sitio', validators=[DataRequired(), Length(max=160)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=2000)])
    monto_acordado = DecimalField('Monto acordado (MXN)', validators=[Optional(), NumberRange(min=0)], places=2)


class PlanPagoForm(FlaskForm):
    """Configura el plan de pagos de un cliente. Se define el monto total y,
    o bien el número de parcialidades, o bien una fecha de fin (de la que se
    calcula cuántas hay)."""
    FRECUENCIAS = [
        ('quincenal_15_fin', 'Quincenal (días 15 y último de cada mes)'),
        ('mensual', 'Mensual (próximamente)'),
        ('semanal', 'Semanal (próximamente)'),
    ]

    monto_total = DecimalField('Monto total (MXN)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    frecuencia = SelectField('Frecuencia', choices=FRECUENCIAS, default='quincenal_15_fin')
    fecha_inicio = DateField('Fecha de inicio (1er vencimiento)', validators=[DataRequired()])
    num_parcialidades = IntegerField('Número de parcialidades', validators=[Optional(), NumberRange(min=1, max=520)])
    fecha_fin = DateField('…o fecha de fin', validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=2000)])

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        # Debe venir el número de parcialidades O una fecha de fin.
        if not self.num_parcialidades.data and not self.fecha_fin.data:
            self.num_parcialidades.errors.append('Indica el número de parcialidades o una fecha de fin.')
            return False
        if self.fecha_fin.data and self.fecha_fin.data < self.fecha_inicio.data:
            self.fecha_fin.errors.append('La fecha de fin no puede ser anterior al inicio.')
            return False
        return True
