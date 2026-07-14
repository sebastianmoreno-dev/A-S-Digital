# Arquitectura del proyecto

## Filosofía

Rutas delgadas, lógica de negocio en servicios, acceso a datos en
repositorios. Ninguna ruta debería tener más de unas pocas líneas de
orquestación — la decisión de negocio vive en `services/`, la consulta
SQL vive en `repositories/`.

```
Petición HTTP
   │
   ▼
Blueprint (routes.py)       ← parsea/valida la request (Flask-WTF), delega
   │
   ▼
Service (services/*.py)     ← reglas de negocio, orquesta repositorios
   │
   ▼
Repository (repositories/*.py) ← única capa que sabe hacer queries SQLAlchemy
   │
   ▼
Model (models/*.py)         ← esquema de datos
```

## Capas

### `app/blueprints/`
Un paquete por área: `main` (páginas públicas), `contact` (formulario),
`admin` (panel interno, con `routes_auth.py`, `routes_leads.py`,
`routes_catalog.py`, `routes_config.py` registrados sobre un único
`admin_bp`). Cada blueprint de formulario trae su propio `forms.py`
(Flask-WTF) — la validación de estructura/tipos vive ahí; las reglas de
negocio (¿existe el servicio? ¿está activo?) viven en el service.

### `app/services/`
- `contact_service.py` — orquesta sanitizar → guardar → loguear → notificar por correo.
- `auth_service.py` — login/logout, lockout por fuerza bruta, registro de sesión.
- `email_service.py` — envío en background thread + registro de resultado.
- `catalog_service.py`, `config_service.py` — CRUD del catálogo/configuración.

### `app/repositories/`
Encapsulan toda consulta SQLAlchemy. Nada fuera de `repositories/`
debería escribir un `Model.query...` directo salvo casos de lectura
simple en rutas de solo-lectura del panel (dashboard, listados) donde
añadir un repositorio sería una capa vacía.

### `app/validators/`
`sanitizers.py` (bleach — elimina HTML/JS de cualquier input) y
`contact_validators.py` (honeypot + tiempo mínimo firmado con
`itsdangerous`). Puramente funciones, sin acceso a BD.

### `app/middlewares/`
- `security_headers.py` — configura Flask-Talisman (CSP, HSTS, etc.) y fija `Permissions-Policy`.
- `rate_limit.py` — inicializa Flask-Limiter, rechaza IPs en lista negra (`before_request`), y en el handler de 429 escala a bloqueo automático tras N violaciones.
- `request_logger.py` — `log_evento()`, el único punto que escribe en `bitacora_eventos`.

### `app/decorators/`
`permission_required(clave)` — exige sesión (Flask-Login) + permiso RBAC.

### `app/models/`
Un archivo por dominio (ver `docs/DATABASE.md` para el diccionario
completo). `app/models/future/` contiene los módulos todavía sin
blueprint (blog, portafolio, CRM, tickets, chat, newsletter, adjuntos)
— el esquema ya existe para no requerir migraciones destructivas
cuando se implementen.

### `app/utils/`
`ip.py` (IP real detrás de Cloudflare vía `CF-Connecting-IP`),
`security.py` (hash de contraseñas argon2id, generación/hash de
tokens), `mailer.py` (arma asunto/cuerpo de los correos del formulario,
sin enviarlos).

## Por qué esta separación

- **Testear sin HTTP:** los tests de `contact_service` no necesitan un
  cliente Flask; se prueban con un objeto de aplicación y datos en memoria.
- **Cambiar de ORM/proveedor de correo sin tocar rutas:** todo el
  conocimiento de "cómo" vive en repositories/utils; las rutas y
  servicios solo conocen el "qué".
- **Auditar seguridad en un solo lugar:** todo el input que llega del
  usuario pasa por `validators/` antes de tocar un modelo.

## Flujo del formulario de contacto (extremo a extremo)

1. `GET /contacto` → `main.contacto` arma un `ContactForm` con las
   choices reales de `servicios`/`rangos_presupuesto` (activos, desde
   BD) y un `form_ts` firmado con la hora de renderizado.
2. `POST /contacto/enviar` (`contact.enviar`):
   - Flask-Limiter ya aplicó el rate limit antes de que el código de la
     vista se ejecute.
   - Se chequea honeypot y tiempo mínimo — si alguno dispara, se
     responde como éxito sin persistir nada (no delata la detección).
   - `ContactForm.validate_on_submit()` — validación de tipos/formato.
   - `contact_service.registrar_contacto(...)` — sanitiza, valida que
     el servicio exista/esté activo, persiste el `Contacto`, escribe en
     bitácora, y dispara los dos correos (admin + cliente) en threads
     de background.
3. La respuesta al usuario no espera al envío de correo — vuelve en
   cuanto el `Contacto` está en BD.

## Flujo del panel admin

`Flask-Login` gestiona la sesión; cada login exitoso/fallido se
registra en `intentos_login` (para el lockout) y en `bitacora_eventos`
(auditoría). `sesiones_admin` guarda un registro adicional por sesión
para poder listarlas/revocarlas a futuro. Las rutas de gestión usan
`@permission_required('clave')`, resuelto contra `rol.permisos`.
