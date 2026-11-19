"""
Settings de VERIFICACIÓN del paquete FND-03.

Artefacto de test del módulo `usuarios`: extienden los settings de test del
proyecto con lo que A0 todavía no ha registrado en `config/settings/base.py`
(archivo compartido, propiedad de A0).

Lo que A0 debe replicar en `config/settings/base.py` (ver la evidencia del
paquete FND-03, sección "Solicitudes a A0"):

```python
LOCAL_APPS = [..., "modules.usuarios"]
AUTH_USER_MODEL = "usuarios.Usuario"
NINJA_EXTRA["INJECTOR_MODULES"] = [..., "modules.usuarios.di.UsuariosModule"]
```

Mientras eso no ocurra, los comandos de verificación del paquete se ejecutan
con `--settings=modules.usuarios.tests.settings_usuarios` (o `--ds=` en
pytest). El resto del proyecto sigue usando `config.settings.*`.
"""

import os

from config.settings.test import *  # noqa: F401,F403

#: App del módulo de identidad.
#:
#: IDEMPOTENCIA (reconciliación A0 de FND-01, 2026-11-19): A0 ya registró la
#: app de forma permanente en `config/settings/base.py`. Registrar la MISMA app
#: dos veces en `INSTALLED_APPS` es un error de Django ("Application labels
#: aren't unique"), así que el overlay sólo añade lo que falta.
if "modules.usuarios" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "modules.usuarios"]  # noqa: F405

#: El modelo de usuario del proyecto es `usuarios.Usuario`.
AUTH_USER_MODEL = "usuarios.Usuario"

#: Cableado de inyecci��n de dependencias del módulo.
_injector_modules = list(NINJA_EXTRA.get("INJECTOR_MODULES", []))  # noqa: F405
if "modules.usuarios.di.UsuariosModule" not in _injector_modules:
    _injector_modules.append("modules.usuarios.di.UsuariosModule")
NINJA_EXTRA = {
    **NINJA_EXTRA,  # noqa: F405
    "INJECTOR_MODULES": _injector_modules,
}

#: Ruta de una base SQLite en FICHERO para el ensayo de migraciones
#: (`USUARIOS_SQLITE_PATH`). Sin la variable, la base es en memoria, como en
#: `config.settings.test`.
SQLITE_PATH = os.environ.get("USUARIOS_SQLITE_PATH", "")
if SQLITE_PATH:
    DATABASES = {
        **DATABASES,  # noqa: F405
        "default": {
            **DATABASES["default"],  # noqa: F405
            "NAME": SQLITE_PATH,
        },
    }
