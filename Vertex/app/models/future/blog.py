"""Blog / noticias. 'Noticias' reutiliza esta misma tabla con tipo='noticia'
en vez de duplicar una estructura casi idéntica."""
from app.extensions import db
from app.models.base import TimestampMixin, UpdatedAtMixin

blog_post_categorias = db.Table(
    'blog_post_categorias',
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_posts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('blog_categoria_id', db.Integer, db.ForeignKey('blog_categorias.id', ondelete='CASCADE'), primary_key=True),
)


class BlogCategoria(db.Model):
    __tablename__ = 'blog_categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    posts = db.relationship('BlogPost', secondary=blog_post_categorias, back_populates='categorias')


class BlogPost(db.Model, TimestampMixin, UpdatedAtMixin):
    __tablename__ = 'blog_posts'

    TIPOS = ('articulo', 'noticia')
    ESTADOS = ('borrador', 'publicado')

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    resumen = db.Column(db.String(500), nullable=True)
    contenido_html = db.Column(db.Text, nullable=False)
    imagen_portada = db.Column(db.String(255), nullable=True)

    autor_admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id', ondelete='SET NULL'), nullable=True)
    tipo = db.Column(db.Enum(*TIPOS, name='blog_tipo'), default='articulo', nullable=False, index=True)
    estado = db.Column(db.Enum(*ESTADOS, name='blog_estado'), default='borrador', nullable=False, index=True)
    publicado_en = db.Column(db.DateTime, nullable=True)

    autor = db.relationship('Administrador')
    categorias = db.relationship('BlogCategoria', secondary=blog_post_categorias, back_populates='posts')
