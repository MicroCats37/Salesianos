"""La ENTREGA de la tienda: el otro dueño del derecho.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `RN-M07` · `FR-05` §5

GIVEN  un pedido PAGADO con su entrega pendiente
WHEN   el operador canjea la credencial de entrega
THEN   el pedido queda ENTREGADO con su acta y la entrega parcial se deniega.
"""

import asyncio

import pytest

from modules.marketplace.domain.constants import EstadoEntregaPedido
from modules.marketplace.domain.models import EntregaPedido
from modules.validaciones.domain.exceptions import CantidadExcedidaError
from modules.validaciones.domain.schemas.validacion_schemas import ConfirmarTicketData
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


def test_la_entrega_consume_el_pedido_y_deja_su_acta(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido pagado con la entrega pendiente · WHEN se confirma su
    credencial · THEN el pedido queda ENTREGADO con su acta (`RN-M07`)."""
    resultado = asyncio.run(
        confirmar_flujo._confirmar(
            str(usuario_admin.id),
            None,
            ConfirmarTicketData(
                codigo=ticket_entrega.codigo,
                idempotency_key="clave-entrega-1",
            ),
        )
    )

    assert resultado.cantidad_consumida == 2
    assert resultado.cantidad_restante == 0

    pedido_pagado.refresh_from_db()
    assert pedido_pagado.estado_entrega == EstadoEntregaPedido.ENTREGADO
    assert EntregaPedido.objects.filter(pedido=pedido_pagado).count() == 1


def test_la_entrega_parcial_se_deniega(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido de dos unidades · WHEN se confirma una sola · THEN se
    deniega: la entrega parcial no está ratificada (`PD-03` abierto)."""
    with pytest.raises(CantidadExcedidaError):
        asyncio.run(
            confirmar_flujo._confirmar(
                str(usuario_admin.id),
                None,
                ConfirmarTicketData(
                    codigo=ticket_entrega.codigo,
                    idempotency_key="clave-entrega-2",
                    cantidad=1,
                ),
            )
        )

    pedido_pagado.refresh_from_db()
    assert pedido_pagado.estado_entrega == EstadoEntregaPedido.PENDIENTE
    assert EntregaPedido.objects.filter(pedido=pedido_pagado).count() == 0


def test_la_entrega_de_un_pedido_no_pagado_se_deniega(
    confirmar_flujo, ticket_entrega, pedido_pagado, usuario_admin
):
    """GIVEN un pedido NO pagado · WHEN se canjea · THEN se deniega: entregar
    exige pagado (`RN-M07`)."""
    from modules.marketplace.domain.constants import EstadoPedido
    from modules.validaciones.domain.exceptions import DerechoRevocadoError

    pedido_pagado.estado = EstadoPedido.PENDIENTE
    pedido_pagado.save(update_fields=["estado", "updated_at"])

    with pytest.raises(DerechoRevocadoError):
        asyncio.run(
            confirmar_flujo._confirmar(
                str(usuario_admin.id),
                None,
                ConfirmarTicketData(
                    codigo=ticket_entrega.codigo,
                    idempotency_key="clave-entrega-3",
                ),
            )
        )
