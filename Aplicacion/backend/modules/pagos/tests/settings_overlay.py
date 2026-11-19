"""Overlay de configuración para la VERIFICACIÓN del paquete FND-04.

**Por qué existe.** `config/settings/base.py` y `config/api.py` son de A0 y
este paquete (A2) NO los edita: el registro permanente se pide como evidencia
(peticiones A0-02, A0-03 y A0-04 del evidence de FND-04). Para poder VERIFICAR
los módulos `commerce` y `pagos` sin tocar la configuración compartida, este
overlay replica el registro que A0 debe hacer de forma permanente:

    INSTALLED_APPS += ["modules.usuarios", "modules.commerce", "modules.pagos"]
    AUTH_USER_MODEL = "usuarios.Usuario"
    NINJA_EXTRA["INJECTOR_MODULES"] += [
        "modules.usuarios.di.UsuariosModule",
        "modules.commerce.di.CommerceModule",
        "modules.pagos.di.PagosModule",
    ]

`usuarios` se registra porque `Compra.persona` es una FK a `usuarios.Persona`
y porque `AUTH_USER_MODEL` del objetivo es `usuarios.Usuario` (FND-03).

**Uso** (workdir `Aplicacion/backend`):

    $env:DJANGO_SETTINGS_MODULE = "modules.pagos.tests.settings_overlay"
    python -m pytest modules/commerce/tests modules/pagos/tests -q
    python manage.py makemigrations --check --dry-run --settings=modules.pagos.tests.settings_overlay
    python manage.py migrate --settings=modules.pagos.tests.settings_overlay

`pytest-django` da prioridad al `--ds` / a la variable de entorno sobre el
valor de `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`), así
que con la variable de entorno fijada el overlay gana.

**Base de datos.** Por defecto usa la SQLite en memoria de
`config.settings.test`. Si se define `PAGOS_SQLITE_PATH`, la base es un
archivo SQLite en esa ruta: sirve para comprobar el REPLAY de migraciones
sobre una base real y luego eliminar el archivo.

**Retiro.** A0 debe sustituir este overlay por el registro permanente en
`config/settings/base.py` y eliminar este archivo.
"""

import os

from config.settings.test import *  # noqa: F401,F403

# ── Apps de los módulos del paquete FND-04 (+ `usuarios`, de FND-03) ───────
INSTALLED_APPS = [  # noqa: F405
    *INSTALLED_APPS,  # noqa: F405
    *[
        app
        for app in ("modules.usuarios", "modules.commerce", "modules.pagos")
        if app not in INSTALLED_APPS  # noqa: F405
    ],
]

#: El modelo de usuario del proyecto es `usuarios.Usuario`.
AUTH_USER_MODEL = "usuarios.Usuario"

# ── Wiring de DI ───────────────────────────────────────────────────────────
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": [
        *NINJA_EXTRA.get("INJECTOR_MODULES", []),  # noqa: F405
        *[
            module
            for module in (
                "modules.usuarios.di.UsuariosModule",
                "modules.commerce.di.CommerceModule",
                "modules.pagos.di.PagosModule",
            )
            if module not in NINJA_EXTRA.get("INJECTOR_MODULES", [])  # noqa: F405
        ],
    ],
}

# ── Base de datos opcional sobre archivo ───────────────────────────────────
_sqlite_path = os.environ.get("PAGOS_SQLITE_PATH")
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
