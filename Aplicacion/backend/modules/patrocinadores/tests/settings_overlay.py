"""Overlay de configuración para la VERIFICACIÓN del paquete DOM-08.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A8) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-01 y A0-02 de la evidencia de DOM-08). Para poder VERIFICAR el
módulo sin tocar la configuración compartida, este overlay replica el
registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.patrocinadores"]
    NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.patrocinadores.di.PatrocinadoresModule"]

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.patrocinadores.tests.settings_overlay"
    uv run python -m pytest modules/patrocinadores/tests -q
    uv run python manage.py makemigrations --check --dry-run --settings=modules.patrocinadores.tests.settings_overlay

`pytest-django` da prioridad a la variable de entorno sobre el valor de
`pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), así que con
la variable de entorno fijada el overlay gana.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`.

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── URLconf sin la barra de desarrollo ──────────────────────────────────────
#
# `config/settings/test.py` deja `DEBUG = True` y `config/urls.py` mete las
# rutas de `debug_toolbar` cuando `DEBUG` está activo. La app `debug_toolbar`
# NO está en `INSTALLED_APPS` (sólo `config/settings/development.py` la
# añade), así que con `DEBUG = True` el `ROOT_URLCONF` no se puede importar.
#
# El overlay apaga `DEBUG` para que los comandos de `manage.py` puedan correr
# sobre esta configuración. Es un defecto de A0 (`config/settings/test.py` +
# `config/urls.py`): DOM-05 lo pidió como A0-03 y el paquete DOM-08 lo repite.
DEBUG = False  # noqa: F405

# ── App del módulo `patrocinadores` ─────────────────────────────────────────
#
# IDEMPOTENCIA: A0 puede registrar la app de forma permanente en
# `config/settings/base.py`. Registrar la MISMA app dos veces en
# `INSTALLED_APPS` es un error de Django ("Application labels aren't
# unique"), así que el overlay sólo añade lo que falta.
if "modules.patrocinadores" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.patrocinadores"]  # noqa: F405

# ── Wiring de DI ────────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.patrocinadores.di.PatrocinadoresModule" not in _injector_modules:
    _injector_modules.append("modules.patrocinadores.di.PatrocinadoresModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Almacenamiento de archivos ───────────────────────────────────────────────
#
# `STORAGES` del objetivo ya declara la entrada `default` (A0 lo aplicó en la
# reconciliación de DOM-01/DOM-04), pero el overlay la replica de forma
# idempotente para no depender de ese estado: sin `default` NO existe
# `default_storage` y ningún módulo puede persistir imágenes.
_storages = dict(STORAGES)  # noqa: F405
_storages.setdefault(
    "default",
    {"BACKEND": "django.core.files.storage.FileSystemStorage"},
)
STORAGES = _storages  # noqa: F405

# ── Dominios de media autorizados ───────────────────────────────────────────
#
# `MEDIA_DOMAINS` es la lista de primeros segmentos de ruta autorizados
# (FR-06 §2.2). `patrocinadores` YA está en el registro de A0; el overlay lo
# replica de forma idempotente para que el módulo sea verificable aunque el
# registro cambie.
_media_dominios = list(MEDIA_DOMAINS)  # noqa: F405
if "patrocinadores" not in _media_dominios:
    _media_dominios.append("patrocinadores")
MEDIA_DOMAINS = _media_dominios  # noqa: F405

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("PATROCINADORES_SQLITE_PATH")
if _sqlite_path:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
            "OPTIONS": {"timeout": 30},
        }
    }
