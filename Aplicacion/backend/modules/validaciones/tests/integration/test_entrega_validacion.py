"""La ENTREGA de la tienda: el otro dueño del derecho.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `RN-M07` · `FR-05` §5

GIVEN  un pedido PAGADO con su entrega pendiente
WHEN   el operador canjea la credencial de entrega
THEN   el pedido queda ENTREGADO con su acta y la entrega parcial se deniega.

**Por qué `transaction=True`.** El canje es un flujo ASYNC: su acceso al ORM
happens en `sync_to_async`, con otra conexión. Con el `atomic()` de un test no
transaccional, esa conexión segunda encuentra el bloqueo de escritura de la
primera (`database table is locked`). El patrón del proyecto para flujos async
es `django_db(transaction=True)` con tests `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import pytest

from modules.marketplace.domain.constants import EstadoEntregaPedido
from modules.validaciones.domain.exceptions import CantidadExcedidaError
from modules.validaciones.domain.schemas.validacion_schemas import ConfirmarTicketData
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.tests.fixtures.validacion_fixtures import (
    cambiar_estado_pedido,
    contar_entregas_de,
    estado_entrega_de,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


async def test_la_entrega_consume_el_pedido_y_deja_su_acta(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido pagado con la entrega pendiente · WHEN se confirma su
    credencial · THEN el pedido queda ENTREGADO con su acta (`RN-M07`)."""
    resultado = await confirmar_flujo._confirmar(
        str(usuario_admin.id),
        None,
        ConfirmarTicketData(
            codigo=ticket_entrega.codigo,
            idempotency_key="clave-entrega-1",
        ),
    )

    assert resultado.cantidad_consumida == 2
    assert resultado.cantidad_restante == 0

    assert await estado_entrega_de(pedido_pagado) == EstadoEntregaPedido.ENTREGADO
    assert await contar_entregas_de(pedido_pagado) == 1


async def test_la_entrega_parcial_se_deniega(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido de dos unidades · WHEN se confirma una sola · THEN se
    deniega: la entrega parcial no está ratificada (`PD-03` abierto)."""
    with pytest.raises(CantidadExcedidaError):
        await confirmar_flujo._confirmar(
            str(usuario_admin.id),
            None,
            ConfirmarTicketData(
                codigo=ticket_entrega.codigo,
                idempotency_key="clave-entrega-2",
                cantidad=1,
            ),
        )

    assert await estado_entrega_de(pedido_pagado) == EstadoEntregaPedido.PENDIENTE
    assert await contar_entregas_de(pedido_pagado) == 0


async def test_la_entrega_de_un_pedido_no_pagado_se_deniega(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido NO pagado · WHEN se canjea · THEN se deniega: entregar
    exige pagado (`RN-M07`)."""
    from modules.marketplace.domain.constants import EstadoPedido
    from modules.validaciones.domain.exceptions import DerechoRevocadoError

    await cambiar_estado_pedido(pedido_pagado, EstadoPedido.PENDIENTE)

    with pytest.raises(DerechoRevocadoError):
        await confirmar_flujo._confirmar(
            str(usuario_admin.id),
            None,
            ConfirmarTicketData(
                codigo=ticket_entrega.codigo,
                idempotency_key="clave-entrega-3",
            ),
        )
