"""Registro de fixtures del módulo `pagos`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

from modules.pagos.tests.fixtures.pagos_fixtures import (  # noqa: F401
    clave_comercio,
    compra,
    injector,
    intento,
    orden_pago,
    otra_persona,
    persona,
    sin_clave_comercio,
    usuario_ajeno,
    usuario_comprador,
)
