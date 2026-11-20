"""
`conftest.py` raíz de los tests del módulo `usuarios`.

`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3: el `conftest.py` raíz
re-exporta TODAS las fixtures de `fixtures/` para que pytest las descubra.

DEPENDENCIA DE A0 (paquete FND-03): el módulo `modules.usuarios` todavía NO
está registrado en `INSTALLED_APPS` ni `AUTH_USER_MODEL` porque
`config/settings/base.py` es un archivo compartido propiedad de A0. Sin ese
registro, los modelos del módulo no se pueden instanciar y sus tests no se
pueden NI COLECTAR.

Mientras A0 no aplique el registro, los tests de este paquete se ejecutan
con los settings de verificación del propio paquete:

    $env:PYTEST_ADDOPTS = "--ds=modules.usuarios.tests.settings_usuarios"
    python -m pytest modules/usuarios/tests -q

Sin esa variable, los módulos de test se OMITEN (no se ejecutan a medias ni
se reportan como un paso falso) y queda un marcador visible que falla en
cuanto A0 aplique el registro.
"""

import sys

from django.apps import apps

#: ¿El módulo de identidad está registrado como app Django?
MODULO_REGISTRADO = apps.is_installed("modules.usuarios")

#: Módulos de test que dependen del modelo de identidad.
MODULOS_DE_TEST = (
    "test_concurrencia_persona.py",
    "test_persona_identidad.py",
    "test_persona_resolucion.py",
    "test_titularidad.py",
    "test_auth_login.py",
    "test_auth_sesion.py",
    "test_auth_registro.py",
)

if not MODULO_REGISTRADO:
    sys.stderr.write(
        "\n[FND-03] `modules.usuarios` NO está registrado en INSTALLED_APPS: "
        "sus tests se OMITEN.\n"
        "         A0 debe aplicar el registro (ver la evidencia del paquete "
        "FND-03) o ejecutarlos con\n"
        "         `--ds=modules.usuarios.tests.settings_usuarios`.\n\n"
    )


def pytest_ignore_collect(collection_path, config):
    """Omite la recolección de los tests que dependen del modelo.

    Sin el registro de la app, importar esos módulos falla al instanciar los
    modelos: es mejor omitir la recolección que romper la sesión de tests
    del resto del proyecto.
    """
    if MODULO_REGISTRADO:
        return None
    if collection_path.name in MODULOS_DE_TEST:
        return True
    if collection_path.is_dir() and collection_path.name == "integration":
        return True
    return None


if MODULO_REGISTRADO:
    from modules.usuarios.tests.fixtures.auth_fixtures import (  # noqa: F401
        cliente_con_sesion,
        cuenta_inactiva,
        superusuario_tecnico,
    )
    from modules.usuarios.tests.fixtures.persona_fixtures import (  # noqa: F401
        api_client,
        api_usuarios,
        auth_client,
        consulta_documento_client,
        cuenta_con_persona,
        cuenta_sin_persona,
        persona_creada,
        persona_registrada_sin_cuenta,
        usuario_administrador,
        usuario_normal,
    )
