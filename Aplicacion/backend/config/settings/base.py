"""
Base settings — compartidas por todos los entornos.
"""

import environ
from pathlib import Path
from datetime import timedelta

# ── Paths ────────────────────────────────────────────────────
# Como base.py está en config/settings/base.py, subimos 3 niveles para llegar a la raíz
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environ ──────────────────────────────────────────────────
env = environ.Env(DEBUG=(bool, False))
# Lee .env si existe (para desarrollo local). En Docker, las vars vienen via env_file.
# read_env() no falla si el archivo no existe — es seguro llamarlo siempre.
environ.Env.read_env(BASE_DIR / ".env", raise_error=False)

# ── Seguridad ────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

# ── Hosts permitidos ─────────────────────────────────────────
# Fallback permisivo para desarrollo; production.py overridea si es necesario
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# ── Apps ─────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "ninja_extra",
    "ninja_jwt",
    "ninja_jwt.token_blacklist",
    "simple_history",
    "corsheaders",
    "django_q",
    "nested_admin",
]

LOCAL_APPS = [
    'import_export',

    "core",
    # ── Apps de dominio (A0 · reconciliación FND-01) ───────────────────────
    # Sólo se registran las apps COMPLETADAS. El orden respeta el GRAFO DE
    # MIGRACIONES del objetivo, que es la autoridad:
    #   `usuarios` (AUTH_USER_MODEL + grupos funcionales)
    #     → `pagos`    (swappable_dependency(AUTH_USER_MODEL))
    #       → `commerce` (FK a `pagos` y a `usuarios`)
    # `eventos` no depende de ninguna app de dominio, por eso va delante.
    # Una app INACABADA no se registra: su modelo no existe todavía y el
    # registro sólo puede referring a una app completada y verificada.
    #
    # Reconciliación A0 de DOM-01 y DOM-04 (2026-11-19):
    #   `salesianos_fest` (DOM-01) → depende de `eventos.0001` y
    #                               `usuarios.0002`; se registra DESPUÉS de
    #                               `commerce` por petición explícita de DOM-01
    #                               (A0-01), que es el orden del grafo.
    #   `marketplace`      (DOM-04) → depende de `eventos.0001`.
    # Ninguna app INACABADA (`pases`, `beneficios`, `validaciones`,
    # `patrocinadores`, `competencias`, `administracion`) se registra.
    "modules.eventos",
    "modules.usuarios",
    "modules.pagos",
    "modules.commerce",
    "modules.salesianos_fest",
    "modules.marketplace",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ───────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "ninja.compatibility.files.fix_request_files_middleware",
    "core.middleware.static_cache.StaticDataCacheMiddleware",
  ]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Contraseñas ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

STORAGES = {
    # ── `default` (A0 · reconciliación DOM-04, petición A0-04) ─────────────
    # Django 5 exige la entrada `default`: sin ella `default_storage` NO
    # existe y `ImageField`/los módulos que escriben media fallan con
    # `InvalidStorageError: Could not find config for 'default' in
    # settings.STORAGES`. No es un fallo de negocio: ningún módulo puede
    # persistir imágenes.
    #
    # El backend es el `FileSystemStorage` LOCAL de Django: escribe bajo
    # `MEDIA_ROOT`, que es el VOLUMEN PERSISTENTE del contrato de media
    # (FREEZE-MD-1.0.0 · FR-06 §2.1). No se inventa almacenamiento en la
    # nube, ni rutas, ni credenciales.
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# ── Internacionalización ─────────────────────────────────────
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ── Static & Media ───────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ── Media (multimedia) ───────────────────────────────────────
# Freeze: FREEZE-MD-1.0.0 · evidence/contracts/FR-06-media.md
# Contrato: core/media.py (allowlist, tamaño, firma, ruta y protocolo).
#
# MEDIA_ROOT es un VOLUMEN PERSISTENTE: guarda estado durable de negocio,
# no es un caché. MEDIA_URL se sirve sin CDN (DEC-14).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Allowlist MIME. `image/svg+xml` está EXCLUIDO a propósito: puede llevar
# script embebido.
MEDIA_ALLOWED_MIME_TYPES = env.list(
    "MEDIA_ALLOWED_MIME_TYPES",
    default=["image/jpeg", "image/png", "image/webp"],
)

# Tamaño máximo por archivo: 5 MiB.
MEDIA_MAX_SIZE_BYTES = env.int("MEDIA_MAX_SIZE_BYTES", default=5 * 1024 * 1024)

# Dominios autorizados como primer segmento de la ruta
# MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><ext>.
MEDIA_DOMAINS = env.list(
    "MEDIA_DOMAINS",
    default=["productos", "patrocinadores"],
)

# Límites de dimensión en píxeles. Los límites EXACTOS por tipo están
# PENDIENTES de ratificación (GOV-01-OPEN-10, owner A0 + A5). Con 0 la
# comprobación no se ejecuta; con un valor > 0 el hook de core/media.py
# rechaza los archivos fuera de rango (pixel bomb).
MEDIA_MIN_DIMENSION = env.int("MEDIA_MIN_DIMENSION", default=0)
MEDIA_MAX_DIMENSION = env.int("MEDIA_MAX_DIMENSION", default=0)

# Copia de seguridad del volumen de media. La POLÍTICA está PENDIENTE de
# ratificación (GOV-01-OPEN-09, owner A0 + producto): este módulo no inventa
# rutas, credenciales ni ventanas. El interruptor permite activar la copia
# cuando la política esté definida; por defecto no hay copia y el
# comportamiento es explícito, no silencioso.
MEDIA_BACKUP_ENABLED = env.bool("MEDIA_BACKUP_ENABLED", default=False)
MEDIA_BACKUP_ROOT = env("MEDIA_BACKUP_ROOT", default="")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth ─────────────────────────────────────────────────────

# El modelo de usuario del objetivo es `usuarios.Usuario` (FR-03 §1.2).
#
# ORDEN: se fija ANTES de la primera migración del objetivo. Un cambio de
# `AUTH_USER_MODEL` sobre una base ya migrada con `auth.User` exige una base
# nueva (o cirugía de migraciones de `auth`); la base del objetivo está vacía.
AUTH_USER_MODEL = "usuarios.Usuario"

# ── Evento activo (FEST) ─────────────────────────────────────
# `EVENTO_ACTIVO_NOMBRE` SE RETIRA (FREEZE-ED-1.0.0 · FR-02 §2.4 · D-01).
#
# El supuesto de scope "un evento activo por nombre" queda reemplazado por el
# ORDEN ÚNICO de resolución de edición que vive en el módulo `eventos`
# (edición explícita → edición activa del actor → única `PUBLICADA` → error).
# No hay reemplazo en settings: el scope se resuelve en el dominio, y un
# setting global volvería a introducir exactamente el supuesto que FR-02 §2.4
# rechaza.

# ── JWT (django-ninja-jwt) ───────────────────────────────────
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Login propio en /api/auth/login/ — no usamos el built-in de ninja-jwt
}

# ── Django Ninja Extra ───────────────────────────────────────
NINJA_EXTRA = {
    # ── Extensión de DI (A0 · reconciliación FND-01) ───────────────────────
    # Sólo los módulos de DI de las apps COMPLETADAS. El orden importa: las
    # dependencias se registran antes que sus dependientes
    # (`usuarios` → `pagos` → `commerce`); `eventos` es independiente.
    # Ningún módulo de un dominio inacabado se registra: su wiring no existe.
    "INJECTOR_MODULES": [
        "modules.usuarios.di.UsuariosModule",
        "modules.eventos.di.EventosModule",
        "modules.pagos.di.PagosModule",
        "modules.commerce.di.CommerceModule",
        # DOM-01 (A0-01) · DOM-04 (A0-02): sólo los módulos de DI de apps
        # COMPLETADAS. El orden mantiene las dependencias delante de sus
        # dependientes (`usuarios` → `pagos` → `commerce`).
        "modules.salesianos_fest.di.SalesianosFestModule",
        "modules.marketplace.di.MarketplaceModule",
    ]
}

# ── Django Q2 (Workers) ──────────────────────────────────────
Q_CLUSTER = {
    "name": "generic-workers",
    "workers": 4,
    "recycle": 500,
    "timeout": 60,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

# ---------------------------------------------------------------------------
# Database — Override with USE_SQLITE=true for lightweight testing (e.g. Docker)
# ---------------------------------------------------------------------------
import os

if os.environ.get("USE_SQLITE", "").lower() in ("1", "true", "yes"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_PATH", ":memory:"),
        }
    }
else:
    # PostgreSQL — production.py debería overridear, pero dejamos helper limpio.
    # Lee DB_* con defaults razonables. Puerto interno estándar: 5432.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="salesianos_db"),
            "USER": env("DB_USER", default="salesianos_user"),
            "PASSWORD": env("DB_PASSWORD", default="changeme"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
        }
    }

# ---------------------------------------------------------------------------
# Izipay Perú — Web Core 2.0 Payment Gateway (izipay.pe)
#
# Credentials obtained from: https://sandbox-panel.izipay.pe/
#   - IZIPAY_SHOP_ID: Código de comercio / tienda
#   - IZIPAY_KEY: Clave pública del botón de pagos (public key)
#   - IZIPAY_KEY_HASH: Clave secreta HMAC-SHA256 (keyHash) del comercio.
#     Es la ÚNICA forma de verificar que un payload de pago lo emitió el
#     proveedor. Vacía = la verificación de firma NO está disponible: el
#     relay del navegador queda sin firma verificable y el canal servidor a
#     servidor rechaza las notificaciones (fallo cerrado). El release debe
#     quedar bloqueado hasta que esta clave esté configurada.
# ---------------------------------------------------------------------------

IZIPAY_SHOP_ID = env("IZIPAY_SHOP_ID", default="")
IZIPAY_KEY = env("IZIPAY_KEY", default="")
IZIPAY_KEY_HASH = env("IZIPAY_KEY_HASH", default="")
IZIPAY_API_URL = env(
    "IZIPAY_API_URL",
    default="https://sandbox-api-pw.izipay.pe"
)
IZIPAY_CALLBACK_URL = env(
    "IZIPAY_CALLBACK_URL",
    default="https://salesianos.example.com/api/pagos/izipay/callback"
)

# ---------------------------------------------------------------------------
# Aprobación manual de pagos (administrador)
#
# Interruptor de despliegue de la capacidad "aprobación manual de pago".
#
# El modelo, la auditoría y la verificación de pagos se despliegan PRIMERO
# (migraciones aditivas, sin backfill) y la acción se habilita DESPUÉS: de
# ese modo el rollback es desactivar este flag — la auditoría nunca se
# borra.
#
# Deshabilitado por defecto: la superficie de escritura sólo existe cuando
# la organización la habilita de forma explícita.
# ---------------------------------------------------------------------------

PAGO_MANUAL_APROBACION_ENABLED = env(
    "PAGO_MANUAL_APROBACION_ENABLED",
    default=False,
)

# ---------------------------------------------------------------------------
# Pases de fiesta (catálogo independiente)
#
# Interruptor de despliegue de la capacidad "pases de fiesta".
#
# El modelo (`Pase` / `PasePrecio`) y el catálogo público se despliegan
# PRIMERO (migraciones aditivas, sin backfill) y la capacidad se habilita
# DESPUÉS: de ese modo el rollback es desactivar este flag — las tablas nunca
# se borran porque conservan la auditoría de venta.
#
# Deshabilitado por defecto: la superficie de compra sólo existe cuando la
# organización la habilita de forma explícita.
# ---------------------------------------------------------------------------

PASES_FIESTA_ENABLED = env(
    "PASES_FIESTA_ENABLED",
    default=False,
)
