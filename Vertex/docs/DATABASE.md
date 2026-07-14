# Diccionario de datos

Esquema completo en [`schema.sql`](../schema.sql) (DDL de referencia,
MySQL 8 InnoDB/utf8mb4). Los modelos SQLAlchemy en `app/models/` son
la fuente de verdad; este documento es la guía de lectura.

Convenciones: `id` autoincremental como PK en todas las tablas,
`creado_en`/`actualizado_en` en UTC, `activo`/soft-delete donde una
fila puede quedar obsoleta pero está referenciada por historial
(servicios, rangos, administradores).

## 1. Staff / autenticación interna

No hay tabla de "usuarios" públicos — el sitio no tiene ni tendrá
registro de clientes. Solo el equipo interno (staff) se autentica.

| Tabla | Propósito |
|---|---|
| `roles` | Roles del panel (ej. "Administrador"). |
| `permisos` | Permisos atómicos (`leads.view`, `leads.edit`, `catalogo.manage`, `config.manage`, `admins.manage`). |
| `rol_permisos` | N:M roles↔permisos. |
| `administradores` | Cuentas de staff. `activo` es soft-delete — nunca se borra un admin (rompería FKs de auditoría/asignación). Incluye columnas de 2FA listas mas no activas. |
| `sesiones_admin` | Una fila por sesión de login — permite listar/revocar sesiones activas a futuro. |
| `intentos_login` | Cada intento de login (éxito o fallo) — sostiene el lockout por fuerza bruta. |
| `tokens` | Tokens de un solo uso (`password_reset`, `email_verification`); se guarda solo el hash SHA-256, nunca el token en claro. El CSRF de Flask-WTF **no** vive aquí — es firmado en la sesión del navegador. |
| `admin_2fa_codigos_respaldo` | Códigos de respaldo para 2FA — esquema listo, flujo aún no activado en el panel. |

## 2. Catálogo (administrable desde el panel)

| Tabla | Propósito |
|---|---|
| `servicios` | Reemplaza el `<select>` hardcodeado del formulario. `activo`/`orden` controlan qué se muestra y en qué orden. |
| `rangos_presupuesto` | Igual, para el rango de presupuesto del formulario. |

## 3. Formulario de contacto

| Tabla | Propósito |
|---|---|
| `contactos` | Un lead por fila. Guarda nombre/empresa/email/teléfono/servicio/presupuesto/descripción + metadatos de la request (`ip`, `user_agent`, `creado_en`) + gestión interna (`estado`, `observaciones_internas`, `fecha_seguimiento`, `administrador_asignado_id`). `estado` es un CRM básico de una sola tabla: `nuevo → en_seguimiento → cotizado → ganado/perdido/descartado`. |

## 4. Bitácora

| Tabla | Propósito |
|---|---|
| `bitacora_eventos` | Tabla **única** de eventos del sistema (envíos exitosos, errores, accesos, bloqueos, cambios administrativos, errores internos) — se prefirió una tabla genérica con `tipo_evento`/`nivel`/`extra` (JSON) sobre una tabla por módulo, para poder auditar todo ordenado por fecha en un solo lugar. |

## 5. Rate limiting y bloqueo de IPs

| Tabla | Propósito |
|---|---|
| `rate_limit_violaciones` | Auditoría de límites excedidos. El conteo en tiempo real vive en Redis (Flask-Limiter) — esta tabla solo se escribe cuando un límite se excede, no en cada request. |
| `lista_negra_ip` | IPs bloqueadas, manual o automáticamente (tras N violaciones seguidas). `bloqueo_permanente` + `expira_en` distinguen bloqueo temporal de definitivo. |

## 6. Comunicaciones

| Tabla | Propósito |
|---|---|
| `correos_enviados` | Historial de todo correo que la app intenta mandar (notificación admin, confirmación cliente, recuperación de contraseña a futuro). Guarda `estado`, `intentos` y `error_detalle` — es el rastro de auditoría del envío en background. |

## 7. Configuración del sitio

| Tabla | Propósito |
|---|---|
| `configuracion_sitio` | Clave/valor para datos operativos que cambian seguido (correo de contacto, teléfono, WhatsApp, redes sociales, horarios). **Deliberadamente no incluye credenciales/API keys reales** — esas van en variables de entorno del servidor; guardarlas en una tabla editable desde un panel web las expondría a cualquiera con acceso de escritura a esa pantalla sin necesidad real. |

## 8. Escalabilidad futura

Tablas creadas ahora (esquema listo, sin blueprint/UI todavía) para
que agregar el módulo no requiera una migración destructiva:

| Tabla(s) | Módulo futuro |
|---|---|
| `blog_posts`, `blog_categorias`, `blog_post_categorias` | Blog **y** noticias (`blog_posts.tipo = 'articulo'\|'noticia'` — se reutiliza la misma tabla en vez de duplicar estructura). |
| `portafolio_proyectos`, `portafolio_imagenes` | Portafolio de proyectos realizados, con galería. |
| `testimonios` | Testimonios de clientes (`calificacion` 1–5 con `CHECK`). |
| `preguntas_frecuentes` | FAQ. |
| `clientes`, `proyectos_cliente`, `cotizaciones`, `reuniones_agenda` | CRM básico: un lead (`contactos`) se puede convertir en `cliente`; de ahí se derivan proyectos, cotizaciones formales y agenda de reuniones. |
| `tickets_soporte`, `ticket_mensajes` | Sistema de tickets. |
| `chat_conversaciones`, `chat_mensajes` | Chat en vivo (web o WhatsApp). |
| `newsletter_suscriptores` | Suscripción a newsletter con confirmación por token. |
| `archivos_adjuntos` | Adjuntos reutilizables entre tickets/proyectos/cotizaciones vía `(entidad_tipo, entidad_id)` — patrón polimórfico simple; la integridad de esa relación se valida en la app, no con una FK de BD (trade-off documentado). |

No existe una tabla de "estadísticas de visitas": se decidió no
reinventar analítica que Cloudflare Analytics ya cubre gratis y sin
costo de escritura por request.

## Normalización y restricciones

- 3FN como mínimo: sin datos repetidos entre tablas (ej. el nombre del
  servicio vive solo en `servicios`, `contactos` solo guarda la FK).
- Toda FK declara su `ON DELETE`: `RESTRICT` donde borrar rompería
  historial de negocio (ej. `contactos.servicio_id`), `SET NULL` donde
  la relación es opcional/de auditoría (ej. `contactos.administrador_asignado_id`),
  `CASCADE` donde el hijo no tiene sentido sin el padre (ej.
  `rol_permisos`, `sesiones_admin`).
- Índices en toda FK y en las columnas de filtro/orden más comunes
  (`estado`, `creado_en`, `ip`, `activo`).
- `ENUM` de MySQL para estados cerrados (`contactos.estado`,
  `correos_enviados.estado`, etc.) — se emulan como `CHECK` en SQLite
  para desarrollo, vía SQLAlchemy.
