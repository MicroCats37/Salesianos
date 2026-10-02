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
    "core_application",
    "modules.usuarios",
    "modules.inscripciones",  # Inscripciones FEST
    "modules.pagos",          # Pagos Izipay
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
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# ── Internacionalización ─────────────────────────────────────
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ── Static& Media ───────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth ─────────────────────────────────────────────────────
AUTH_USER_MODEL = "usuarios.Usuario"

# ── Evento activo (FEST) ─────────────────────────────────────
# Inscripciones FEST — único evento activo por edición.
# El frontend NO envía `evento_id`: el backend lo resuelve desde esta constante.
EVENTO_ACTIVO_NOMBRE = env("EVENTO_ACTIVO_NOMBRE", default="Salesianos FEST 2026")

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
    "INJECTOR_MODULES": [
        "modules.usuarios.di.UsuariosModule",
        "modules.inscripciones.di.InscripcionesModule",
        "modules.pagos.di.PagosModule",
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
# ---------------------------------------------------------------------------

IZIPAY_SHOP_ID = env("IZIPAY_SHOP_ID", default="")
IZIPAY_KEY = env("IZIPAY_KEY", default="")
IZIPAY_API_URL = env(
    "IZIPAY_API_URL",
    default="https://sandbox-api-pw.izipay.pe"
)
IZIPAY_CALLBACK_URL = env(
    "IZIPAY_CALLBACK_URL",
    default="https://salesianos.example.com/api/pagos/izipay/callback"
)
