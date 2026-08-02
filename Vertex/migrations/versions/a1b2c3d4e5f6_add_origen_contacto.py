"""Agrega columna 'origen' a contactos (de dónde llegó el lead)

Revision ID: a1b2c3d4e5f6
Revises: 6b7334131575
Create Date: 2026-08-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6b7334131575'
branch_labels = None
depends_on = None


ORIGENES = ('formulario_web', 'referido', 'redes_sociales', 'contacto_directo', 'otro')


def upgrade():
    bind = op.get_bind()

    # En Postgres el tipo ENUM no se crea automáticamente al hacer add_column
    # (a diferencia de create_table), así que se crea explícitamente. En sqlite
    # el ENUM se compila como VARCHAR + CHECK y esto es un no-op.
    if bind.dialect.name == 'postgresql':
        sa.Enum(*ORIGENES, name='contacto_origen').create(bind, checkfirst=True)

    origen_col_type = sa.Enum(*ORIGENES, name='contacto_origen', create_type=False)

    with op.batch_alter_table('contactos', schema=None) as batch_op:
        # server_default respalda las filas ya existentes en producción:
        # todo lead previo queda marcado como 'formulario_web'.
        batch_op.add_column(
            sa.Column('origen', origen_col_type, server_default='formulario_web', nullable=False)
        )
        batch_op.create_index(batch_op.f('ix_contactos_origen'), ['origen'], unique=False)


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table('contactos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_contactos_origen'))
        batch_op.drop_column('origen')

    if bind.dialect.name == 'postgresql':
        sa.Enum(name='contacto_origen').drop(bind, checkfirst=True)
