# Seguridad implementada

## 1. Validación de backend

`app/blueprints/contact/forms.py` (`ContactForm`, Flask-WTF/WTForms) y
`app/blueprints/admin/forms.py` validan tipo, longitud y formato de
cada campo en el servidor. Las validaciones HTML5/JS del template
(`required`, `type="email"`, etc.) son solo UX — el backend nunca
confía en ellas ni asume que llegaron intactas.

## 2. Sanitización (anti-XSS)

`app/validators/sanitizers.py::strip_html()` usa `bleach` para eliminar
por completo cualquier etiqueta/atributo HTML o JavaScript de todo
campo de texto libre antes de guardarlo (nombre, empresa, descripción
del proyecto). Además, el autoescape de Jinja2 (activo por defecto)
protege también al renderizar esos datos en el panel admin —
defensa en profundidad, no un único punto de fallo.

## 3. SQL Injection

Cero SQL concatenado en todo el proyecto. Todo acceso a datos pasa por
SQLAlchemy ORM (`app/repositories/`), que parametriza las consultas
automáticamente. `schema.sql` es solo un archivo de referencia/bootstrap,
nunca se ejecuta con datos de usuario interpolados.

## 4. CSRF

`Flask-WTF` (`CSRFProtect`) está activo globalmente
(`app/extensions.py` + `csrf.init_app(app)` en `app/__init__.py`).
Todo formulario incluye `{{ form.hidden_tag() }}` (o un
`csrf_token` manual en los formularios de configuración que no usan
una clase `FlaskForm`, ver `templates/admin/config.html`). Un POST sin
token válido responde `400`.

## 5. Rate limiting

`Flask-Limiter` (`app/middlewares/rate_limit.py`), backend Redis en
producción (memoria en desarrollo si no hay `REDIS_URL`):

- `/contacto/enviar`: 5/minuto, 20/hora, 100/día por IP real.
- La IP se resuelve vía `CF-Connecting-IP` (`app/utils/ip.py`), no
  `request.remote_addr` directo — así el límite es por visitante real
  y no por la IP del proxy de Cloudflare.

## 6. Honeypot

Campo oculto `website` (`ContactForm.website`), posicionado fuera de
pantalla por CSS (`.hp-field` — `position: absolute; left: -9999px`,
no `display:none`, porque algunos bots simples sí respetan
`display:none`/`visibility:hidden` y lo saltan). Si llega con
contenido, el envío se descarta **silenciosamente**: se responde igual
que un éxito y se registra en bitácora, sin persistir el lead ni
delatar al bot que fue detectado.

## 7. Tiempo mínimo

`app/validators/contact_validators.py::make_form_timestamp()` firma
(con `itsdangerous`, usando `SECRET_KEY`) la hora de renderizado del
formulario en un campo oculto. Al recibir el POST,
`is_submission_too_fast()` recalcula el tiempo transcurrido a partir
del token firmado — no de un campo editable por el cliente, así que no
se puede falsear abriendo devtools y cambiando un input. Menos de
`CONTACT_MIN_SECONDS` (5s por defecto) se trata igual que el honeypot.

## 8. Registro de actividad

`app/middlewares/request_logger.py::log_evento()` es el único punto
que escribe en `bitacora_eventos`: fecha, IP, user-agent, tipo de
evento, nivel (`info`/`warning`/`error`/`critical`) y descripción. Se
registra en: envíos exitosos/fallidos del formulario, detección de bot
(honeypot/tiempo mínimo), accesos bloqueados por lista negra, límites
de rate limiting excedidos, bloqueos automáticos, y login/logout/lockout
del panel admin.

## 9. Bloqueo automático

`app/middlewares/rate_limit.py`: cada vez que una IP excede el rate
limit se escribe una fila en `rate_limit_violaciones`. Si acumula
`RATE_LIMIT_VIOLATIONS_BEFORE_BLOCK` violaciones (default 3) dentro de
`RATE_LIMIT_BLOCK_HOURS` horas (default 24), la IP se inserta
automáticamente en `lista_negra_ip` con bloqueo temporal. Un
`before_request` global rechaza con `403` cualquier request de una IP
en lista negra vigente, en cualquier ruta del sitio (no solo el
formulario). El mismo mecanismo de auto-bloqueo se reutiliza para
intentos de login fallidos repetidos contra el panel admin.

## 10. Headers de seguridad

`app/middlewares/security_headers.py` (Flask-Talisman):

| Header | Valor |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' fonts.googleapis.com 'unsafe-inline'; font-src fonts.gstatic.com; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; ...` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (solo se envía sobre HTTPS) |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Deshabilita geolocalización, cámara, micrófono, pagos, USB, etc. |

**Nota sobre `'unsafe-inline'` en `style-src`:** las plantillas del
sitio usan `style="..."` inline extensivamente (heredado del diseño
original). Se limpiaron todos los manejadores de eventos inline
(`onmouseover`/`onmouseout`/`onclick`) del proyecto y se movieron a
CSS puro (`:hover`) o a `main.js` con `addEventListener` — eso es lo
que permite tener `script-src 'self'` **sin** `'unsafe-inline'`, que es
la parte que realmente importa para prevenir XSS (ejecución de script
arbitrario). Quitar `'unsafe-inline'` de `style-src` también
requeriría refactorizar cientos de atributos `style=""` a clases CSS o
usar nonces por request — se documenta como mejora futura, no bloquea
la protección real contra XSS.

## 11. Compatibilidad con Cloudflare

- `ProxyFix` (Werkzeug) confía en el proxy delante de Flask
  (`TRUSTED_PROXY_COUNT`) para `X-Forwarded-For`/`X-Forwarded-Proto` —
  necesario para que Flask sepa que la conexión real es HTTPS y para
  que Flask-Talisman/las cookies `Secure` funcionen bien detrás de un
  proxy.
- La IP real del visitante se toma de `CF-Connecting-IP` (que
  Cloudflare siempre inyecta), no de `X-Forwarded-For` ni
  `remote_addr` directo.
- `Flask-Talisman` se configura con `force_https=False` en producción:
  el redirect HTTP→HTTPS lo hace Cloudflare ("Always Use HTTPS"), para
  evitar un loop de redirects si el modo SSL de Cloudflare es
  "Flexible". Se recomienda usar modo **"Full (strict)"** con
  certificado válido en el origen.
- No se implementa rate limiting "agresivo" a nivel de red ni un WAF
  propio — Cloudflare (Bot Fight Mode, WAF, DDoS Protection) ya cubre
  esa capa; el rate limiting de la app es control de abuso a nivel de
  aplicación (por formulario/IP), complementario y no conflictivo.

## 12. Validaciones del lado del cliente

Los `required`, `type="email"`, `pattern` etc. en `templates/contacto.html`
existen únicamente para dar feedback inmediato en el navegador. Cada
regla tiene su equivalente server-side (§1) y el servidor nunca asume
que el HTML/JS del cliente no fue modificado o evitado por completo
(ej. un POST directo con `curl`).

## Contraseñas y tokens

- Contraseñas de administradores: **argon2id** (`argon2-cffi`), no
  MD5/SHA ni siquiera bcrypt plano — es el algoritmo recomendado
  actualmente por OWASP para hashing de contraseñas.
- Tokens de sesión/recuperación de contraseña: generados con
  `secrets.token_urlsafe()`, y solo se persiste su hash SHA-256 en BD
  (`app/utils/security.py`) — un volcado de la base de datos no expone
  tokens utilizables.

## Qué falta para "producción completa" (fuera de alcance de esta entrega)

- Verificación de correo / 2FA de administradores: esquema de BD listo
  (`administradores.two_factor_*`, `admin_2fa_codigos_respaldo`,
  `tokens`), flujo todavía no implementado en el panel.
- CSP sin `'unsafe-inline'` en `style-src` (ver §10).
- Cola de tareas real (Celery+Redis) para envío de correo, si el
  volumen crece lo suficiente como para que el hilo en background dentro
  del proceso Flask deje de ser suficiente (ver `docs/ARCHITECTURE.md`).
