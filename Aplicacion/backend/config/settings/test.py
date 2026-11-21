"""
Test settings.
"""
import os
from datetime import timedelta

# Los tests NUNCA dependen de una credencial de base de datos: el motor se fija
# en SQLite ANTES de importar `base` (que, si no, exigiría `DB_PASSWORD` en el
# entorno). Explícito y determinista, con o sin `.env` presente (A0-VER03-05).
os.environ["USE_SQLITE"] = "true"

from .base import *  # noqa: E402,F403,F405

DEBUG = True

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
SECRET_KEY = "django-insecure-test-secret-key-1234567890"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 30,
            'isolation_level': None,
        },
    }
}

# ── CIP Simulator ────────────────────────────────────────────
# En tests usamos el simulador para no depender del API externo real
CIP_USE_SIMULATOR = True
CONSULTA_EXTERNA_USE_SIMULATOR = True

# ── Notificaciones (Mock) ───────────────────────────────────
NOTI_EMULATOR_ENABLED = True
NOTI_URL = "http://mock-noti"
NOTI_APP_ID = 999

# Deshabilitamos middleware pesado para tests unitarios
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]

# ── JWT ──────────────────────────────────────────────────────
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Login propio en /api/auth/login/ — no usamos el built-in de ninja-jwt
}
