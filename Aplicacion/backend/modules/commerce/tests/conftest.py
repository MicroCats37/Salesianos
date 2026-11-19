"""Registro de fixtures del módulo `commerce`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3
"""

from modules.commerce.tests.fixtures.activacion_fakes import (  # noqa: F401
    ActivadorDominioFake,
    activador,
    registro_activadores,
)
from modules.commerce.tests.fixtures.commerce_fixtures import (  # noqa: F401
    intencion,
    injector,
    linea,
    otra_persona,
    persona,
)
