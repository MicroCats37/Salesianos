"""Overlay de configuración para la VERIFICACIÓN del paquete XCT-02.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete NO los edita (`00-contrato-global-de-apply.md`, "Shared Files").
El registro permanente se pide como evidencia (`A0-XCT02-01`). Para poder
VERIFICAR el módulo `administracion` sin tocar la configuración compartida,
este overlay replica el registro que A0 debe hacer:

    INSTALLED_APPS += ["modules.administracion"]
    NINJA_EXTRA["INJECTOR_MODULES"] += [
        "modules.administracion.di.AdministracionModule",
    ]

`modules.eventos`, `modules.usuarios`, `modules.pagos`, `modules.commerce`,
`modules.salesianos_fest` y `modules.marketplace` ya están registrados de
forma permanente por A0: este módulo depende de ellos, no al revés.

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.administracion.tests.settings_overlay"
    python -m pytest modules/administracion/tests -q

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── App del módulo `administracion` ──────────────────────────────────────────
if "modules.administracion" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.administracion"]  # noqa: F405

# ── Wiring de DI ────────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.administracion.di.AdministracionModule" not in _injector_modules:
    _injector_modules.append("modules.administracion.di.AdministracionModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Base de datos opcional sobre archivo ────────────────────────────────────
_sqlite_path = os.environ.get("ADMINISTRACION_SQLITE_PATH")
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
