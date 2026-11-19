"""
`conftest.py` de los tests de integración.

`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3: sólo registra los módulos de
fixtures. El registro condicional evita importar los modelos del módulo de
identidad cuando la app todavía no está en `INSTALLED_APPS`
(dependencia pendiente de A0, paquete FND-03).
"""

from django.apps import apps

if apps.is_installed("modules.usuarios"):
    from modules.usuarios.tests.fixtures import persona_fixtures  # noqa: F401
