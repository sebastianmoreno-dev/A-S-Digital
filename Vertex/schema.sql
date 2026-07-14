-- =====================================================================
-- AS Vertex — schema.sql
-- Esquema completo de base de datos (MySQL 8+, InnoDB, utf8mb4)
--
-- Este archivo es la referencia canónica del esquema y sirve para
-- bootstrap manual de un servidor nuevo. En desarrollo/CI el esquema
-- se aplica normalmente vía Flask-Migrate/Alembic (ver migrations/).
-- Los modelos SQLAlchemy en app/models/ son la fuente de verdad;
-- este archivo debe mantenerse en sincronía con ellos.
--
-- Orden de creación: respeta las dependencias de llaves foráneas.
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS as_vertex
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE as_vertex;

-- =====================================================================
-- 1. STAFF / AUTH INTERNO (sin registro público de usuarios)
-- =====================================================================

CREATE TABLE roles (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(60)  NOT NULL,
  descripcion   VARCHAR(255) NULL,
  creado_en     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_roles_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE permisos (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  clave         VARCHAR(80)  NOT NULL,
  descripcion   VARCHAR(255) NULL,
  UNIQUE KEY uq_permisos_clave (clave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rol_permisos (
  rol_id      INT UNSIGNED NOT NULL,
  permiso_id  INT UNSIGNED NOT NULL,
  PRIMARY KEY (rol_id, permiso_id),
  CONSTRAINT fk_rolpermisos_rol     FOREIGN KEY (rol_id)     REFERENCES roles(id)    ON DELETE CASCADE,
  CONSTRAINT fk_rolpermisos_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE administradores (
  id                     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre                 VARCHAR(120) NOT NULL,
  email                  VARCHAR(180) NOT NULL,
  password_hash          VARCHAR(255) NOT NULL,
  rol_id                 INT UNSIGNED NOT NULL,
  activo                 TINYINT(1)   NOT NULL DEFAULT 1,
  two_factor_secret      VARCHAR(64)  NULL,
  two_factor_habilitado  TINYINT(1)   NOT NULL DEFAULT 0,
  ultimo_login_en        DATETIME     NULL,
  creado_en              DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_administradores_email (email),
  KEY ix_administradores_rol (rol_id),
  CONSTRAINT fk_administradores_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sesiones_admin (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  administrador_id  INT UNSIGNED NOT NULL,
  token_hash        CHAR(64)     NOT NULL,
  ip                VARCHAR(45)  NOT NULL,
  user_agent        VARCHAR(255) NULL,
  creado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expira_en         DATETIME     NOT NULL,
  revocada          TINYINT(1)   NOT NULL DEFAULT 0,
  UNIQUE KEY uq_sesionesadmin_token (token_hash),
  KEY ix_sesionesadmin_admin (administrador_id),
  CONSTRAINT fk_sesionesadmin_admin FOREIGN KEY (administrador_id) REFERENCES administradores(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE intentos_login (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email_intentado  VARCHAR(180) NOT NULL,
  ip               VARCHAR(45)  NOT NULL,
  user_agent       VARCHAR(255) NULL,
  exitoso          TINYINT(1)   NOT NULL DEFAULT 0,
  motivo_fallo     VARCHAR(120) NULL,
  creado_en        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_intentoslogin_email (email_intentado),
  KEY ix_intentoslogin_ip (ip),
  KEY ix_intentoslogin_creado (creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tokens (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo              ENUM('password_reset','email_verification') NOT NULL,
  administrador_id  INT UNSIGNED NULL,
  token_hash        CHAR(64)     NOT NULL,
  expira_en         DATETIME     NOT NULL,
  usado             TINYINT(1)   NOT NULL DEFAULT 0,
  ip_solicitante    VARCHAR(45)  NULL,
  creado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_tokens_hash (token_hash),
  KEY ix_tokens_admin (administrador_id),
  CONSTRAINT fk_tokens_admin FOREIGN KEY (administrador_id) REFERENCES administradores(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Nota: el token CSRF de Flask-WTF NO se persiste aquí; vive firmado en
-- la sesión/cookie del navegador y se valida sin tocar la base de datos.

CREATE TABLE admin_2fa_codigos_respaldo (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  administrador_id  INT UNSIGNED NOT NULL,
  codigo_hash       CHAR(64)     NOT NULL,
  usado             TINYINT(1)   NOT NULL DEFAULT 0,
  creado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_2facodigos_admin (administrador_id),
  CONSTRAINT fk_2facodigos_admin FOREIGN KEY (administrador_id) REFERENCES administradores(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Esquema listo para 2FA; el flujo todavía no está activado en el panel.

-- =====================================================================
-- 2. CATÁLOGO (administrable desde el panel — nada hardcodeado en HTML)
-- =====================================================================

CREATE TABLE servicios (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  clave          VARCHAR(60)    NOT NULL,
  nombre         VARCHAR(120)   NOT NULL,
  descripcion    TEXT           NULL,
  precio_desde   DECIMAL(10,2)  NULL,
  activo         TINYINT(1)     NOT NULL DEFAULT 1,
  orden          INT            NOT NULL DEFAULT 0,
  creado_en      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_servicios_clave (clave),
  KEY ix_servicios_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rangos_presupuesto (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  clave          VARCHAR(60)    NOT NULL,
  etiqueta       VARCHAR(120)   NOT NULL,
  monto_min      DECIMAL(10,2)  NULL,
  monto_max      DECIMAL(10,2)  NULL,
  activo         TINYINT(1)     NOT NULL DEFAULT 1,
  orden          INT            NOT NULL DEFAULT 0,
  creado_en      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_rangospresupuesto_clave (clave),
  KEY ix_rangospresupuesto_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 3. FORMULARIO DE CONTACTO
-- =====================================================================

CREATE TABLE contactos (
  id                        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre                    VARCHAR(120) NOT NULL,
  empresa                   VARCHAR(120) NULL,
  email                     VARCHAR(180) NOT NULL,
  telefono                  VARCHAR(30)  NULL,
  servicio_id               INT UNSIGNED NOT NULL,
  rango_presupuesto_id      INT UNSIGNED NULL,
  descripcion_proyecto      TEXT         NOT NULL,
  ip                        VARCHAR(45)  NOT NULL,
  user_agent                VARCHAR(255) NULL,
  estado                    ENUM('nuevo','en_seguimiento','cotizado','ganado','perdido','descartado')
                             NOT NULL DEFAULT 'nuevo',
  observaciones_internas    TEXT         NULL,
  fecha_seguimiento         DATE         NULL,
  administrador_asignado_id INT UNSIGNED NULL,
  creado_en                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY ix_contactos_email (email),
  KEY ix_contactos_estado (estado),
  KEY ix_contactos_creado (creado_en),
  KEY ix_contactos_ip (ip),
  KEY ix_contactos_servicio (servicio_id),
  KEY ix_contactos_rango (rango_presupuesto_id),
  KEY ix_contactos_admin_asignado (administrador_asignado_id),
  CONSTRAINT fk_contactos_servicio FOREIGN KEY (servicio_id)  REFERENCES servicios(id)          ON DELETE RESTRICT,
  CONSTRAINT fk_contactos_rango    FOREIGN KEY (rango_presupuesto_id) REFERENCES rangos_presupuesto(id) ON DELETE SET NULL,
  CONSTRAINT fk_contactos_admin    FOREIGN KEY (administrador_asignado_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 4. BITÁCORA (tabla única de eventos del sistema)
-- =====================================================================

CREATE TABLE bitacora_eventos (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo_evento       VARCHAR(60)  NOT NULL,
  nivel             ENUM('info','warning','error','critical') NOT NULL DEFAULT 'info',
  administrador_id  INT UNSIGNED NULL,
  ip                VARCHAR(45)  NULL,
  user_agent        VARCHAR(255) NULL,
  descripcion       TEXT         NULL,
  extra             JSON         NULL,
  creado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_bitacora_tipo_creado (tipo_evento, creado_en),
  KEY ix_bitacora_ip (ip),
  KEY ix_bitacora_admin (administrador_id),
  CONSTRAINT fk_bitacora_admin FOREIGN KEY (administrador_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 5. RATE LIMITING Y LISTA NEGRA
-- =====================================================================
-- El conteo en tiempo real de solicitudes vive en Redis (Flask-Limiter).
-- rate_limit_violaciones es solo el rastro de auditoría: se escribe
-- cuando un límite se excede, no en cada request.

CREATE TABLE rate_limit_violaciones (
  id                 INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ip                 VARCHAR(45)  NOT NULL,
  endpoint           VARCHAR(120) NOT NULL,
  limite_excedido    VARCHAR(40)  NOT NULL,
  num_solicitudes    INT          NOT NULL,
  ventana_inicio     DATETIME     NOT NULL,
  ventana_fin        DATETIME     NOT NULL,
  resulto_en_bloqueo TINYINT(1)   NOT NULL DEFAULT 0,
  creado_en          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_ratelimitviol_ip (ip),
  KEY ix_ratelimitviol_creado (creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lista_negra_ip (
  id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ip                   VARCHAR(45)  NOT NULL,
  motivo               VARCHAR(255) NOT NULL,
  bloqueado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  bloqueo_permanente   TINYINT(1)   NOT NULL DEFAULT 0,
  expira_en            DATETIME     NULL,
  creado_por_admin_id  INT UNSIGNED NULL,
  activo               TINYINT(1)   NOT NULL DEFAULT 1,
  creado_en            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_listanegra_ip (ip),
  KEY ix_listanegra_activo (activo),
  CONSTRAINT fk_listanegra_admin FOREIGN KEY (creado_por_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 6. COMUNICACIONES
-- =====================================================================

CREATE TABLE correos_enviados (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  destinatario   VARCHAR(180) NOT NULL,
  asunto         VARCHAR(255) NOT NULL,
  tipo           ENUM('notificacion_admin','confirmacion_cliente','password_reset','otro') NOT NULL,
  contacto_id    INT UNSIGNED NULL,
  estado         ENUM('enviado','fallido','pendiente') NOT NULL DEFAULT 'pendiente',
  error_detalle  TEXT NULL,
  intentos       INT UNSIGNED NOT NULL DEFAULT 0,
  enviado_en     DATETIME NULL,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_correosenviados_estado (estado),
  KEY ix_correosenviados_contacto (contacto_id),
  CONSTRAINT fk_correosenviados_contacto FOREIGN KEY (contacto_id) REFERENCES contactos(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 7. CONFIGURACIÓN DEL SITIO
-- =====================================================================
-- Credenciales/API keys reales NO se guardan aquí (van en variables de
-- entorno del servidor). Esta tabla es para datos operativos públicos:
-- correo de contacto, teléfono, WhatsApp, redes sociales, horarios.

CREATE TABLE configuracion_sitio (
  id                       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  clave                    VARCHAR(80)  NOT NULL,
  valor                    TEXT         NULL,
  tipo                     ENUM('texto','numero','booleano','json') NOT NULL DEFAULT 'texto',
  descripcion              VARCHAR(255) NULL,
  categoria                VARCHAR(60)  NULL,
  actualizado_en           DATETIME     NULL,
  actualizado_por_admin_id INT UNSIGNED NULL,
  UNIQUE KEY uq_configuracionsitio_clave (clave),
  KEY ix_configuracionsitio_categoria (categoria),
  CONSTRAINT fk_configuracionsitio_admin FOREIGN KEY (actualizado_por_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- 8. ESCALABILIDAD FUTURA
-- Tablas creadas ahora (esquema listo) para no requerir migraciones
-- destructivas más adelante; sin blueprints/UI todavía.
-- =====================================================================

-- ── Blog / noticias (noticias reutiliza esta tabla con tipo='noticia') ──

CREATE TABLE blog_categorias (
  id      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre  VARCHAR(80) NOT NULL,
  slug    VARCHAR(80) NOT NULL,
  UNIQUE KEY uq_blogcategorias_nombre (nombre),
  UNIQUE KEY uq_blogcategorias_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_posts (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  titulo           VARCHAR(200) NOT NULL,
  slug             VARCHAR(220) NOT NULL,
  resumen          VARCHAR(500) NULL,
  contenido_html   TEXT         NOT NULL,
  imagen_portada   VARCHAR(255) NULL,
  autor_admin_id   INT UNSIGNED NULL,
  tipo             ENUM('articulo','noticia') NOT NULL DEFAULT 'articulo',
  estado           ENUM('borrador','publicado') NOT NULL DEFAULT 'borrador',
  publicado_en     DATETIME NULL,
  creado_en        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_blogposts_slug (slug),
  KEY ix_blogposts_tipo (tipo),
  KEY ix_blogposts_estado (estado),
  CONSTRAINT fk_blogposts_autor FOREIGN KEY (autor_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_post_categorias (
  blog_post_id      INT UNSIGNED NOT NULL,
  blog_categoria_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (blog_post_id, blog_categoria_id),
  CONSTRAINT fk_blogpostcat_post FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_blogpostcat_cat  FOREIGN KEY (blog_categoria_id) REFERENCES blog_categorias(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Portafolio ──

CREATE TABLE portafolio_proyectos (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  titulo          VARCHAR(160) NOT NULL,
  slug            VARCHAR(180) NOT NULL,
  descripcion     TEXT NULL,
  cliente         VARCHAR(160) NULL,
  url             VARCHAR(255) NULL,
  imagen_portada  VARCHAR(255) NULL,
  tecnologias     VARCHAR(255) NULL,
  destacado       TINYINT(1) NOT NULL DEFAULT 0,
  orden           INT NOT NULL DEFAULT 0,
  publicado       TINYINT(1) NOT NULL DEFAULT 0,
  creado_en       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_portafolioproyectos_slug (slug),
  KEY ix_portafolioproyectos_publicado (publicado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE portafolio_imagenes (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  proyecto_id  INT UNSIGNED NOT NULL,
  url          VARCHAR(255) NOT NULL,
  orden        INT NOT NULL DEFAULT 0,
  alt_text     VARCHAR(180) NULL,
  KEY ix_portafolioimagenes_proyecto (proyecto_id),
  CONSTRAINT fk_portafolioimagenes_proyecto FOREIGN KEY (proyecto_id) REFERENCES portafolio_proyectos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Testimonios ──

CREATE TABLE testimonios (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre_cliente VARCHAR(120) NOT NULL,
  empresa        VARCHAR(120) NULL,
  cargo          VARCHAR(120) NULL,
  contenido      TEXT NOT NULL,
  calificacion   TINYINT UNSIGNED NULL,
  foto_url       VARCHAR(255) NULL,
  aprobado       TINYINT(1) NOT NULL DEFAULT 0,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_testimonios_aprobado (aprobado),
  CONSTRAINT ck_testimonios_calificacion CHECK (calificacion IS NULL OR (calificacion BETWEEN 1 AND 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Preguntas frecuentes ──

CREATE TABLE preguntas_frecuentes (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  pregunta   VARCHAR(255) NOT NULL,
  respuesta  TEXT NOT NULL,
  categoria  VARCHAR(80) NULL,
  orden      INT NOT NULL DEFAULT 0,
  activo     TINYINT(1) NOT NULL DEFAULT 1,
  KEY ix_preguntasfrecuentes_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── CRM básico ──

CREATE TABLE clientes (
  id                        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre                    VARCHAR(120) NOT NULL,
  empresa                   VARCHAR(120) NULL,
  email                     VARCHAR(180) NULL,
  telefono                  VARCHAR(30) NULL,
  notas                     TEXT NULL,
  creado_desde_contacto_id  INT UNSIGNED NULL,
  creado_en                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_clientes_email (email),
  KEY ix_clientes_contacto_origen (creado_desde_contacto_id),
  CONSTRAINT fk_clientes_contacto FOREIGN KEY (creado_desde_contacto_id) REFERENCES contactos(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE proyectos_cliente (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cliente_id          INT UNSIGNED NOT NULL,
  nombre              VARCHAR(160) NOT NULL,
  descripcion         TEXT NULL,
  estado              ENUM('propuesta','en_progreso','completado','cancelado') NOT NULL DEFAULT 'propuesta',
  fecha_inicio        DATE NULL,
  fecha_fin_estimada  DATE NULL,
  fecha_fin_real      DATE NULL,
  monto_acordado      DECIMAL(10,2) NULL,
  creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_proyectoscliente_cliente (cliente_id),
  CONSTRAINT fk_proyectoscliente_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cotizaciones (
  id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  contacto_id           INT UNSIGNED NULL,
  cliente_id            INT UNSIGNED NULL,
  servicio_id           INT UNSIGNED NOT NULL,
  monto                 DECIMAL(10,2) NOT NULL,
  moneda                CHAR(3) NOT NULL DEFAULT 'MXN',
  estado                ENUM('borrador','enviada','aceptada','rechazada','expirada') NOT NULL DEFAULT 'borrador',
  valida_hasta          DATE NULL,
  pdf_url               VARCHAR(255) NULL,
  creado_por_admin_id   INT UNSIGNED NULL,
  creado_en             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_cotizaciones_estado (estado),
  KEY ix_cotizaciones_contacto (contacto_id),
  KEY ix_cotizaciones_cliente (cliente_id),
  KEY ix_cotizaciones_servicio (servicio_id),
  CONSTRAINT fk_cotizaciones_contacto FOREIGN KEY (contacto_id) REFERENCES contactos(id) ON DELETE SET NULL,
  CONSTRAINT fk_cotizaciones_cliente  FOREIGN KEY (cliente_id)  REFERENCES clientes(id)  ON DELETE SET NULL,
  CONSTRAINT fk_cotizaciones_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE RESTRICT,
  CONSTRAINT fk_cotizaciones_admin    FOREIGN KEY (creado_por_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reuniones_agenda (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cliente_id          INT UNSIGNED NULL,
  contacto_id         INT UNSIGNED NULL,
  administrador_id    INT UNSIGNED NULL,
  titulo              VARCHAR(160) NOT NULL,
  descripcion         TEXT NULL,
  fecha_hora_inicio   DATETIME NOT NULL,
  fecha_hora_fin      DATETIME NULL,
  ubicacion_o_link    VARCHAR(255) NULL,
  estado              ENUM('programada','confirmada','cancelada','completada') NOT NULL DEFAULT 'programada',
  creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_reunionesagenda_cliente (cliente_id),
  KEY ix_reunionesagenda_contacto (contacto_id),
  KEY ix_reunionesagenda_admin (administrador_id),
  KEY ix_reunionesagenda_fecha (fecha_hora_inicio),
  CONSTRAINT fk_reunionesagenda_cliente  FOREIGN KEY (cliente_id)  REFERENCES clientes(id) ON DELETE SET NULL,
  CONSTRAINT fk_reunionesagenda_contacto FOREIGN KEY (contacto_id) REFERENCES contactos(id) ON DELETE SET NULL,
  CONSTRAINT fk_reunionesagenda_admin    FOREIGN KEY (administrador_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Tickets de soporte ──

CREATE TABLE tickets_soporte (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cliente_id          INT UNSIGNED NULL,
  contacto_id         INT UNSIGNED NULL,
  asunto              VARCHAR(200) NOT NULL,
  descripcion         TEXT NOT NULL,
  estado              ENUM('abierto','en_progreso','resuelto','cerrado') NOT NULL DEFAULT 'abierto',
  prioridad           ENUM('baja','media','alta','urgente') NOT NULL DEFAULT 'media',
  asignado_admin_id   INT UNSIGNED NULL,
  creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY ix_ticketssoporte_estado (estado),
  KEY ix_ticketssoporte_cliente (cliente_id),
  KEY ix_ticketssoporte_contacto (contacto_id),
  KEY ix_ticketssoporte_asignado (asignado_admin_id),
  CONSTRAINT fk_ticketssoporte_cliente  FOREIGN KEY (cliente_id)  REFERENCES clientes(id)  ON DELETE SET NULL,
  CONSTRAINT fk_ticketssoporte_contacto FOREIGN KEY (contacto_id) REFERENCES contactos(id) ON DELETE SET NULL,
  CONSTRAINT fk_ticketssoporte_admin    FOREIGN KEY (asignado_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ticket_mensajes (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ticket_id   INT UNSIGNED NOT NULL,
  autor_tipo  ENUM('cliente','admin') NOT NULL,
  autor_id    INT UNSIGNED NULL,
  mensaje     TEXT NOT NULL,
  creado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_ticketmensajes_ticket (ticket_id),
  CONSTRAINT fk_ticketmensajes_ticket FOREIGN KEY (ticket_id) REFERENCES tickets_soporte(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Chat en vivo (web / WhatsApp) ──

CREATE TABLE chat_conversaciones (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  contacto_id  INT UNSIGNED NULL,
  cliente_id   INT UNSIGNED NULL,
  canal        ENUM('web','whatsapp') NOT NULL DEFAULT 'web',
  iniciado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cerrado_en   DATETIME NULL,
  KEY ix_chatconversaciones_contacto (contacto_id),
  KEY ix_chatconversaciones_cliente (cliente_id),
  CONSTRAINT fk_chatconversaciones_contacto FOREIGN KEY (contacto_id) REFERENCES contactos(id) ON DELETE SET NULL,
  CONSTRAINT fk_chatconversaciones_cliente  FOREIGN KEY (cliente_id)  REFERENCES clientes(id)  ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chat_mensajes (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  conversacion_id   INT UNSIGNED NOT NULL,
  remitente_tipo    ENUM('visitante','admin','bot') NOT NULL,
  mensaje           TEXT NOT NULL,
  creado_en         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_chatmensajes_conversacion (conversacion_id),
  CONSTRAINT fk_chatmensajes_conversacion FOREIGN KEY (conversacion_id) REFERENCES chat_conversaciones(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Newsletter ──

CREATE TABLE newsletter_suscriptores (
  id                 INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email              VARCHAR(180) NOT NULL,
  nombre             VARCHAR(120) NULL,
  confirmado         TINYINT(1) NOT NULL DEFAULT 0,
  token_confirmacion VARCHAR(64) NULL,
  suscrito_en        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  dado_de_baja_en    DATETIME NULL,
  UNIQUE KEY uq_newslettersuscriptores_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Archivos adjuntos (reutilizables entre módulos) ──
-- Patrón polimórfico simple vía (entidad_tipo, entidad_id): sin FK real
-- de BD sobre entidad_id porque apunta a distintas tablas según
-- entidad_tipo. Trade-off documentado: la integridad de esa relación
-- se valida en la capa de aplicación, no en la base de datos.

CREATE TABLE archivos_adjuntos (
  id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre_original      VARCHAR(255) NOT NULL,
  nombre_almacenado    VARCHAR(255) NOT NULL,
  ruta_o_url           VARCHAR(500) NOT NULL,
  mime_type            VARCHAR(120) NULL,
  tamano_bytes         INT UNSIGNED NULL,
  entidad_tipo         VARCHAR(40) NOT NULL,
  entidad_id           INT UNSIGNED NOT NULL,
  subido_por_admin_id  INT UNSIGNED NULL,
  creado_en            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_archivosadjuntos_entidad (entidad_tipo, entidad_id),
  CONSTRAINT fk_archivosadjuntos_admin FOREIGN KEY (subido_por_admin_id) REFERENCES administradores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
