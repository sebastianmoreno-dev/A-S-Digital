# AS Vertex — Sitio web + panel administrativo

Sitio corporativo de AS Vertex construido con Flask, MySQL y un panel
administrativo interno para gestionar los leads del formulario de
contacto, el catálogo de servicios y la configuración del sitio.

Documentación técnica completa en [`docs/`](docs/):
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — estructura del proyecto y capas.
- [`docs/DATABASE.md`](docs/DATABASE.md) — diccionario de datos completo.
- [`docs/SECURITY.md`](docs/SECURITY.md) — medidas de seguridad implementadas.

## Stack

- **Backend:** Flask 3, SQLAlchemy, Flask-Migrate (Alembic)
- **Base de datos:** MySQL 8 (PyMySQL) — SQLite como fallback de desarrollo
- **Cache / rate limiting:** Redis (Flask-Limiter)
- **Auth admin:** Flask-Login + argon2id
- **Seguridad:** Flask-WTF (CSRF), Flask-Talisman (headers), bleach (sanitización)
- **Frontend:** HTML + CSS + JavaScript vanilla (Jinja2 templates)
- **Servidor / dominio:** Linux, detrás de Cloudflare (WAF, Bot Fight Mode, HTTPS, DDoS)

## Requisitos

- Python 3.11+
- MySQL 8+ (en producción; SQLite funciona para desarrollo local)
- Redis (en producción; opcional en desarrollo — cae a memoria del proceso)

## Instalación local

```bash
cd Vertex
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash) — usar `venv\Scripts\activate` en cmd
pip install -r requirements.txt

cp .env.example .env
# Editar .env con tus valores (mínimo: SECRET_KEY)
```

### Base de datos

**Desarrollo rápido (SQLite):** no requiere nada más — `DATABASE_URL` cae a
`sqlite:///pixelforge.db` si no está definido, y la app crea las tablas
automáticamente al arrancar (`AUTO_CREATE_DB=True` en desarrollo).

**Con MySQL (recomendado, igual que producción):**

```bash
mysql -u root -p < ../schema.sql          # crea la BD y todas las tablas
# o, preferido: usar las migraciones de Alembic
export DATABASE_URL="mysql+pymysql://usuario:password@localhost/as_vertex"
flask db upgrade
```

### Datos iniciales (roles, permisos, catálogo, primer admin)

```bash
export ADMIN_SEED_EMAIL="tu@correo.com"
export ADMIN_SEED_PASSWORD="una-clave-fuerte"
python scripts/seed.py
```

Es idempotente — se puede correr varias veces sin duplicar datos.

### Levantar el servidor

```bash
python run.py
# o: flask run
```

- Sitio público: http://localhost:5000
- Panel admin: http://localhost:5000/admin/login

## Migraciones (Flask-Migrate / Alembic)

```bash
flask db migrate -m "descripción del cambio"   # genera una nueva migración
flask db upgrade                                # aplica migraciones pendientes
flask db downgrade                              # revierte la última
```

`schema.sql` en la raíz del proyecto es la referencia canónica del
esquema completo (útil para bootstrap manual); debe mantenerse en
sincronía con los modelos de `app/models/` y las migraciones.

## Tests

```bash
pytest
```

Cubre: validación/XSS/SQLi del formulario, CSRF, rate limiting +
auto-bloqueo de IPs, honeypot + tiempo mínimo, headers de seguridad,
y login/lockout del panel admin. Ver [`tests/`](tests/).

## Estructura del proyecto

```
app/
  blueprints/{main,contact,admin}/   Rutas por área — sin lógica de negocio
  services/                          Lógica de negocio
  repositories/                      Acceso a datos (SQLAlchemy)
  validators/                        Validación server-side + sanitización
  middlewares/                       Headers de seguridad, rate limiting, bitácora
  decorators/                        RBAC del panel admin
  models/                            Modelos SQLAlchemy (uno por dominio)
  utils/                             IP real, hashing, construcción de correos
  templates/, static/                Frontend (Jinja2 + CSS/JS vanilla)
migrations/                          Alembic
scripts/seed.py                      Datos iniciales
schema.sql                           DDL completo de referencia
docs/                                Documentación técnica
tests/                                Pruebas automatizadas
```

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para el detalle de
cada capa y por qué está separada así.

## Despliegue en producción (resumen)

1. Servidor Linux con MySQL y Redis corriendo.
2. `.env` con `FLASK_ENV=production`, `DATABASE_URL` a MySQL, `REDIS_URL`,
   `SECRET_KEY` fuerte y credenciales SMTP reales.
3. `flask db upgrade` para aplicar el esquema.
4. `python scripts/seed.py` una sola vez para crear roles/catálogo/admin inicial.
5. Servir con gunicorn detrás de Nginx, y Nginx detrás de Cloudflare
   (HTTPS, WAF, Bot Fight Mode, DDoS Protection — ya configurado en el
   dominio). En Cloudflare: SSL/TLS en modo "Full (strict)" con
   certificado válido en el origen, y "Always Use HTTPS" activado.
6. `TRUSTED_PROXY_COUNT` debe reflejar cuántos proxies hay entre
   Cloudflare y Flask (normalmente 1 con Nginx de por medio).
