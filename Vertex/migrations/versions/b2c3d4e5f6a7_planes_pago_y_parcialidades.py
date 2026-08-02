"""Planes de pago, parcialidades y proyectos_cliente.contacto_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-02 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


FRECUENCIAS = ('quincenal_15_fin', 'mensual', 'semanal', 'personalizada')
PARCIALIDAD_ESTADOS = ('pendiente', 'pagada')


def upgrade():
    bind = op.get_bind()
    es_pg = bind.dialect.name == 'postgresql'

    # En Postgres los tipos ENUM se crean explícitamente y de forma idempotente
    # (checkfirst=True). Los tipos de las columnas se marcan con create_type=False
    # usando postgresql.ENUM — que SÍ respeta ese flag — para que op.create_table
    # NO vuelva a emitir CREATE TYPE (el sa.Enum genérico lo ignora y provoca un
    # 'ya existe un tipo ...'). En sqlite el ENUM se compila como VARCHAR + CHECK.
    if es_pg:
        from sqlalchemy.dialects.postgresql import ENUM as PGEnum
        sa.Enum(*FRECUENCIAS, name='plan_frecuencia').create(bind, checkfirst=True)
        sa.Enum(*PARCIALIDAD_ESTADOS, name='parcialidad_estado').create(bind, checkfirst=True)
        frecuencia_type = PGEnum(*FRECUENCIAS, name='plan_frecuencia', create_type=False)
        parcialidad_estado_type = PGEnum(*PARCIALIDAD_ESTADOS, name='parcialidad_estado', create_type=False)
    else:
        frecuencia_type = sa.Enum(*FRECUENCIAS, name='plan_frecuencia')
        parcialidad_estado_type = sa.Enum(*PARCIALIDAD_ESTADOS, name='parcialidad_estado')

    op.create_table(
        'planes_pago',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('monto_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('moneda', sa.String(length=3), nullable=False),
        sa.Column('frecuencia', frecuencia_type, nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('num_parcialidades', sa.Integer(), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('planes_pago', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_planes_pago_cliente_id'), ['cliente_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_planes_pago_creado_en'), ['creado_en'], unique=False)

    op.create_table(
        'parcialidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('estado', parcialidad_estado_type, nullable=False),
        sa.Column('fecha_pago', sa.Date(), nullable=True),
        sa.Column('pagada_por_admin_id', sa.Integer(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['planes_pago.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pagada_por_admin_id'], ['administradores.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('parcialidades', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_parcialidades_plan_id'), ['plan_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_parcialidades_fecha_vencimiento'), ['fecha_vencimiento'], unique=False)
        batch_op.create_index(batch_op.f('ix_parcialidades_estado'), ['estado'], unique=False)
        batch_op.create_index(batch_op.f('ix_parcialidades_creado_en'), ['creado_en'], unique=False)

    # Trazabilidad sitio/proyecto → lead ganado de origen (aditivo).
    with op.batch_alter_table('proyectos_cliente', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contacto_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_proyectos_cliente_contacto_id', 'contactos', ['contacto_id'], ['id'], ondelete='SET NULL'
        )


def downgrade():
    bind = op.get_bind()
    es_pg = bind.dialect.name == 'postgresql'

    with op.batch_alter_table('proyectos_cliente', schema=None) as batch_op:
        batch_op.drop_constraint('fk_proyectos_cliente_contacto_id', type_='foreignkey')
        batch_op.drop_column('contacto_id')

    op.drop_table('parcialidades')
    op.drop_table('planes_pago')

    if es_pg:
        sa.Enum(name='parcialidad_estado').drop(bind, checkfirst=True)
        sa.Enum(name='plan_frecuencia').drop(bind, checkfirst=True)
