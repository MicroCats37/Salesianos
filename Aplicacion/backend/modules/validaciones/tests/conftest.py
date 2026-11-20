"""Registro de fixtures del módulo `validaciones`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.

Las fixtures de IDENTIDAD y de PASES se REUTILIZAN de su módulo dueño
(`modules/salesianos_fest/tests/fixtures/`): no se copian ni se modifican.
"""

import pytest

from modules.salesianos_fest.tests.fixtures.fest_fixtures import (  # noqa: F401
    edicion_publicada,
    evento,
    persona,
    persona_ajena,
    persona_participante,
    usuario_ajeno,
    usuario_responsable,
)
from modules.salesianos_fest.tests.fixtures.pase_fixtures import (  # noqa: F401
    TOKEN_PASE_FIJO,
    beneficiario_pase,
    compra_pase_pagada,
    compra_pase_pendiente,
    cortesia_pase,
    edicion_con_pases,
    pase,
    usuario_admin,
)
from modules.validaciones.tests.fixtures.validacion_fixtures import (  # noqa: F401
    CODIGO_TICKET_ENTRADA,
    CODIGO_TICKET_ENTREGA,
    categoria_producto,
    pedido_pagado,
    producto,
    ticket_entrada,
    ticket_entrada_revocado,
    ticket_entrega,
)


@pytest.fixture(scope="session")
def injector():
    """El inyector de dependencias del paquete XCT-01.

    Incluye los módulos de DI de los DUEÑOS que este módulo consume:
    `usuarios`, `eventos`, `pagos`, `commerce`, `salesianos_fest` y
    `marketplace`, más el propio `validaciones`.
    """
    from injector import Injector

    from modules.commerce.di import CommerceModule
    from modules.eventos.di import EventosModule
    from modules.marketplace.di import MarketplaceModule
    from modules.pagos.di import PagosModule
    from modules.salesianos_fest.di import SalesianosFestModule
    from modules.usuarios.di import UsuariosModule
    from modules.validaciones.di import ValidacionesModule

    return Injector(
        [
            UsuariosModule,
            EventosModule,
            PagosModule,
            CommerceModule,
            SalesianosFestModule,
            MarketplaceModule,
            ValidacionesModule,
        ]
    )
