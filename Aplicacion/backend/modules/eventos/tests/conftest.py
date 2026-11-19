"""Registro de fixtures del módulo `eventos`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

from modules.eventos.tests.fixtures.eventos_fixtures import (  # noqa: F401
    core_service,
    edicion_borrador,
    edicion_cerrada,
    edicion_publicada,
    edicion_selector,
    evento,
    evento_otro,
    evento_selector,
    scope_service,
)
