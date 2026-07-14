"""Formulario de contacto (Flask-WTF): validación de servidor + CSRF.

Las validaciones HTML5/JS del template son solo UX — esto es lo único
en lo que se confía de verdad.
"""
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

from app.services import catalog_service
from app.validators.contact_validators import make_form_timestamp

TELEFONO_REGEX = r'^[0-9+\-\s()]{7,20}$'


class ContactForm(FlaskForm):
    nombre = StringField(
        'Nombre completo',
        validators=[DataRequired(message='El nombre es requerido.'), Length(max=120)],
    )
    empresa = StringField('Empresa / Negocio', validators=[Optional(), Length(max=120)])
    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message='Ingresa un correo válido.'),
            Email(message='Ingresa un correo válido.'),
            Length(max=180),
        ],
    )
    telefono = StringField(
        'Teléfono',
        validators=[
            Optional(),
            Regexp(TELEFONO_REGEX, message='Ingresa un teléfono válido.'),
            Length(max=30),
        ],
    )

    # Las choices reales (activas, desde BD) se inyectan en la vista.
    servicio_id = SelectField(
        '¿Qué necesitas?', coerce=int, validators=[DataRequired(message='Selecciona un servicio.')]
    )
    rango_presupuesto_id = SelectField('Presupuesto aproximado', coerce=int, validators=[Optional()], default=0)

    descripcion_proyecto = TextAreaField(
        'Cuéntanos tu proyecto',
        validators=[DataRequired(message='La descripción no puede estar vacía.'), Length(max=4000)],
    )

    # ── Antibot (no son parte de la validación normal del form) ──────
    website = StringField('Website', validators=[Optional()])  # honeypot
    form_ts = HiddenField('form_ts')


def crear_formulario_contacto(*, con_timestamp: bool = False) -> ContactForm:
    """Instancia un ContactForm con las choices reales de servicios/rangos
    (activos, desde BD). `con_timestamp=True` es para el render inicial
    del GET /contacto — arma el token antibot de tiempo mínimo."""
    form = ContactForm()
    form.servicio_id.choices = [(s.id, s.nombre) for s in catalog_service.servicios_para_formulario()]
    form.rango_presupuesto_id.choices = [(0, 'Selecciona un rango (opcional)')] + [
        (r.id, r.etiqueta) for r in catalog_service.rangos_para_formulario()
    ]
    if con_timestamp:
        form.form_ts.data = make_form_timestamp()
    return form
