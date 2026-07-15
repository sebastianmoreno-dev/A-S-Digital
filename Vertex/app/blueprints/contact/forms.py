"""Formulario de contacto (Flask-WTF): validación de servidor + CSRF.

Las validaciones HTML5/JS del template son solo UX — esto es lo único
en lo que se confía de verdad.
"""
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

from app.services import catalog_service
from app.translations import lazy_t, t
from app.validators.contact_validators import make_form_timestamp

TELEFONO_REGEX = r'^[0-9+\-\s()]{7,20}$'


class ContactForm(FlaskForm):
    # Los labels de la clase son solo el fallback: se re-etiquetan según
    # el idioma de la sesión en crear_formulario_contacto(). Los mensajes
    # de error usan lazy_t porque a nivel de clase aún no hay request.
    nombre = StringField(
        'Nombre completo',
        validators=[DataRequired(message=lazy_t('form.err.nombre')), Length(max=120)],
    )
    empresa = StringField('Empresa / Negocio', validators=[Optional(), Length(max=120)])
    email = StringField(
        'Correo electrónico',
        validators=[
            DataRequired(message=lazy_t('form.err.email')),
            Email(message=lazy_t('form.err.email')),
            Length(max=180),
        ],
    )
    telefono = StringField(
        'Teléfono',
        validators=[
            Optional(),
            Regexp(TELEFONO_REGEX, message=lazy_t('form.err.telefono')),
            Length(max=30),
        ],
    )

    # Las choices reales (activas, desde BD) se inyectan en la vista.
    servicio_id = SelectField(
        '¿Qué necesitas?', coerce=int, validators=[DataRequired(message=lazy_t('form.err.servicio'))]
    )
    rango_presupuesto_id = SelectField('Presupuesto aproximado', coerce=int, validators=[Optional()], default=0)

    descripcion_proyecto = TextAreaField(
        'Cuéntanos tu proyecto',
        validators=[DataRequired(message=lazy_t('form.err.descripcion')), Length(max=4000)],
    )

    # ── Antibot (no son parte de la validación normal del form) ──────
    website = StringField('Website', validators=[Optional()])  # honeypot
    form_ts = HiddenField('form_ts')


# Campo → clave de traducción de su label (ver es.json / en.json).
_LABEL_KEYS = {
    'nombre': 'form.nombre',
    'empresa': 'form.empresa',
    'email': 'form.email',
    'telefono': 'form.telefono',
    'servicio_id': 'form.servicio',
    'rango_presupuesto_id': 'form.rango',
    'descripcion_proyecto': 'form.descripcion',
}


def crear_formulario_contacto(*, con_timestamp: bool = False) -> ContactForm:
    """Instancia un ContactForm con las choices reales de servicios/rangos
    (activos, desde BD) y los labels en el idioma de la sesión.
    `con_timestamp=True` es para el render inicial del GET /contacto —
    arma el token antibot de tiempo mínimo."""
    form = ContactForm()
    for campo, clave in _LABEL_KEYS.items():
        getattr(form, campo).label.text = t(clave)
    form.servicio_id.choices = [(s.id, s.nombre) for s in catalog_service.servicios_para_formulario()]
    form.rango_presupuesto_id.choices = [(0, t('form.rango_placeholder'))] + [
        (r.id, r.etiqueta) for r in catalog_service.rangos_para_formulario()
    ]
    if con_timestamp:
        form.form_ts.data = make_form_timestamp()
    return form
