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


class LeadForm(FlaskForm):
    estado = SelectField('Estado', choices=[(e, e.replace('_', ' ').title()) for e in Contacto.ESTADOS])
    observaciones_internas = TextAreaField('Observaciones internas', validators=[Optional(), Length(max=4000)])
    fecha_seguimiento = DateField('Fecha de seguimiento', validators=[Optional()])


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
