"""Overlay de configuración para la VERIFICACIÓN del paquete FND-02.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A1) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-02 y A0-03 del evidence de FND-02). Para poder VERIFICAR el
módulo sin tocar la configuración compartida, este overlay replica el
registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.eventos"]
    NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.eventos.di.EventosModule"]

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.eventos.tests.settings_overlay"
    python -m pytest modules/eventos/tests -q
    python manage.py makemigrations --check --dry-run --settings=modules.eventos.tests.settings_overlay
    python manage.py migrate --settings=modules.eventos.tests.settings_overlay

`pytest-django` da prioridad al `--ds` / a la variable de entorno sobre el
valor de `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), así
que con la variable de entorno fijada el overlay gana.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`. Si se define `EVENTOS_SQLITE_PATH`, la base es un
archivo SQLite en esa ruta: sirve para comprobar el REPLAY de migraciones
sobre una base real y luego eliminar el archivo.

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── App del módulo `eventos` ─────────────────────────────────────────────────
#
# IDEMPOTENCIA (reconciliación A0 de FND-01, 2026-11-19): A0 ya registró la
# app de forma permanente en `config/settings/base.py`. Registrar la MISMA app
# dos veces en `INSTALLED_APPS` es un error de Django ("Application labels
# aren't unique"), así que el overlay sólo añade lo que falta.
if "modules.eventos" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.eventos"]  # noqa: F405

# ── Wiring de DI ────────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.eventos.di.EventosModule" not in _injector_modules:
    _injector_modules.append("modules.eventos.di.EventosModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("EVENTOS_SQLITE_PATH")
if _sqlite_path:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
            "OPTIONS": {"timeout": 30},
        }
    }
