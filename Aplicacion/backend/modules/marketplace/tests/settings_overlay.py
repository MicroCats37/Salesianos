"""Overlay de configuración para la VERIFICACIÓN del paquete DOM-04.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A5) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-02 y A0-03 del evidence de DOM-04). Para poder VERIFICAR el
módulo sin tocar la configuración compartida, este overlay replica el
registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.marketplace"]
    NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.marketplace.di.MarketplaceModule"]

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.marketplace.tests.settings_overlay"
    python -m pytest modules/marketplace/tests -q
    python manage.py makemigrations --check --dry-run --settings=modules.marketplace.tests.settings_overlay
    python manage.py migrate --settings=modules.marketplace.tests.settings_overlay

`pytest-django` da prioridad a la variable de entorno sobre el valor de
`pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), así que con
la variable de entorno fijada el overlay gana.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`. Si se define `MARKETPLACE_SQLITE_PATH`, la base es
un archivo SQLite en esa ruta: sirve para comprobar el REPLAY de migraciones
sobre una base real y luego eliminar el archivo.

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
# añade), así que con `DEBUG = True` el `ROOT_URLCONF` no se puede importar y
# `manage.py check` / `manage.py makemigrations` abortan con:
#
#     RuntimeError: Model class debug_toolbar.models.HistoryEntry doesn't
#     declare an explicit app_label and isn't in an application in
#     INSTALLED_APPS.
#
# El overlay apaga `DEBUG` para que los comandos de `manage.py` puedan correr
# sobre esta configuración. Es un defecto de A0 (`config/settings/test.py` +
# `config/urls.py`): se pide como petición A0-03 del evidence de DOM-05.
DEBUG = False  # noqa: F405

# ── App del módulo `marketplace` ────────────────────────────────────────────
#
# IDEMPOTENCIA: A0 puede registrar la app de forma permanente en
# `config/settings/base.py`. Registrar la MISMA app dos veces en
# `INSTALLED_APPS` es un error de Django ("Application labels aren't
# unique"), así que el overlay sólo añade lo que falta.
if "modules.marketplace" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.marketplace"]  # noqa: F405

# ── Wiring de DI ────────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.marketplace.di.MarketplaceModule" not in _injector_modules:
    _injector_modules.append("modules.marketplace.di.MarketplaceModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Almacenamiento de archivos (A0-04) ──────────────────────────────────────
#
# El `STORAGES` del objetivo declara SÓLO la entrada `staticfiles`. Django 5
# necesita también la entrada `default`: sin ella `default_storage` no
# existe y NINGÚN módulo puede escribir media (el error es
# `InvalidStorageError`, no un fallo de negocio).
#
# El overlay replica el ajuste que A0 debe hacer de forma permanente en
# `config/settings/base.py`. MientrAS A0 no lo aplique, el backend objetivo
# NO puede persistir imágenes: por eso la petición A0-04 es BLOQUEANTE para
# el despliegue de la tienda.
_storages = dict(STORAGES)  # noqa: F405
_storages.setdefault(
    "default",
    {"BACKEND": "django.core.files.storage.FileSystemStorage"},
)
STORAGES = _storages  # noqa: F405

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("MARKETPLACE_SQLITE_PATH")
if _sqlite_path:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
            "OPTIONS": {"timeout": 30},
        }
    }
