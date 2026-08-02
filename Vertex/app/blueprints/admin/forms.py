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
