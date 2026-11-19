"""Overlay de configuración para la VERIFICACIÓN del paquete DOM-01.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A3) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-01 y A0-02 de este paquete). Para poder VERIFICAR el módulo
`salesianos_fest` sin tocar la configuración compartida, este overlay
replica el registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.salesianos_fest"]
    NINJA_EXTRA["INJECTOR_MODULES"] += [
        "modules.salesianos_fest.di.SalesianosFestModule",
    ]

`modules.eventos`, `modules.usuarios`, `modules.pagos` y `modules.commerce`
ya están registrados de forma permanente por A0 (reconciliación de FND-01):
este módulo depende de ellos, no al revés.

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.salesianos_fest.tests.settings_overlay"
    python -m pytest modules/salesianos_fest/tests -q
    python manage.py makemigrations --check --dry-run --settings=modules.salesianos_fest.tests.settings_overlay
    python manage.py migrate --settings=modules.salesianos_fest.tests.settings_overlay

`pytest-django` da prioridad al `--ds` / a la variable de entorno sobre el
valor de `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), así
que con la variable de entorno fijada el overlay gana.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`. Si se define `SALESIANOS_FEST_SQLITE_PATH`, la base
es un archivo SQLite en esa ruta: sirve para comprobar el REPLAY de
migraciones sobre una base real y luego eliminar el archivo.

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── App del módulo `salesianos_fest` ────────────────────────────────────────
#
# IDEMPOTENCIA (reconciliación A0 de FND-01, 2026-11-19): A0 ya registró las
# apps completadas de forma permanente en `config/settings/base.py`. Registrar
# la MISMA app dos veces en `INSTALLED_APPS` es un error de Django ("Application
# labels aren't unique"), así que el overlay sólo añade lo que falta.
if "modules.salesianos_fest" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.salesianos_fest"]  # noqa: F405

# ── Wiring de DI ───────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.salesianos_fest.di.SalesianosFestModule" not in _injector_modules:
    _injector_modules.append("modules.salesianos_fest.di.SalesianosFestModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("SALESIANOS_FEST_SQLITE_PATH")
if _sqlite_path:
    DATABASES = {
        **DATABASES,  # noqa: F405
        "default": {
            **DATABASES["default"],  # noqa: F405
            "NAME": _sqlite_path,
            "OPTIONS": {
                **DATABASES["default"].get("OPTIONS", {}),  # noqa: F405
                "timeout": 30,
            },
        },
    }
