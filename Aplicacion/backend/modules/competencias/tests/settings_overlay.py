"""Overlay de configuración para la VERIFICACIÓN del paquete DOM-07.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A6) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-01 y A0-02 de este paquete). Para poder VERIFICAR el módulo
`competencias` sin tocar la configuración compartida, este overlay replica
el registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.competencias"]
    NINJA_EXTRA["INJECTOR_MODULES"] += [
        "modules.competencias.di.CompetenciasModule",
    ]

`modules.eventos`, `modules.usuarios`, `modules.pagos`, `modules.commerce` y
`modules.salesianos_fest` ya están registrados de forma permanente por A0
(reconciliación de FND-01): este módulo depende de ellos, no al revés.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`. Si se define `COMPETENCIAS_SQLITE_PATH`, la base es
un archivo SQLite en esa ruta: sirve para comprobar el REPLAY de migraciones
sobre una base real y luego eliminar el archivo.

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── App del módulo `competencias` ───────────────────────────────────────────
#
# IDEMPOTENCIA: sólo se añade lo que falta, porque registrar la MISMA app
# dos veces en `INSTALLED_APPS` es un error de Django.
if "modules.competencias" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.competencias"]  # noqa: F405

# ── Wiring de DI ───────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.competencias.di.CompetenciasModule" not in _injector_modules:
    _injector_modules.append("modules.competencias.di.CompetenciasModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("COMPETENCIAS_SQLITE_PATH")
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
