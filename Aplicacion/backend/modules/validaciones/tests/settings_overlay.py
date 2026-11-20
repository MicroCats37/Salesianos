"""Overlay de configuración para la VERIFICACIÓN del paquete XCT-01.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete NO los edita (`00-contrato-global-de-apply.md`, "Shared Files").
El registro permanente se pide como evidencia (peticiones A0-01 y A0-02 de
este paquete). Para poder VERIFICAR el módulo `validaciones` sin tocar la
configuración compartida, este overlay replica el registro que A0 debe
hacer:

    INSTALLED_APPS += ["modules.validaciones"]
    NINJA_EXTRA["INJECTOR_MODULES"] += [
        "modules.validaciones.di.ValidacionesModule",
    ]

`modules.eventos`, `modules.usuarios`, `modules.pagos`, `modules.commerce`,
`modules.salesianos_fest` y `modules.marketplace` ya están registrados de
forma permanente por A0: este módulo depende de ellos, no al revés.

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.validaciones.tests.settings_overlay"
    python -m pytest modules/validaciones/tests -q

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── App del módulo `validaciones` ────────────────────────────────────────────
if "modules.validaciones" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.validaciones"]  # noqa: F405

# ── Wiring de DI ────────────────────────────────────────────────────────────
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.validaciones.di.ValidacionesModule" not in _injector_modules:
    _injector_modules.append("modules.validaciones.di.ValidacionesModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

# ── Base de datos opcional sobre archivo ────────────────────────────────────
_sqlite_path = os.environ.get("VALIDACIONES_SQLITE_PATH")
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
