"""Fixtures del módulo de VALIDACIONES (`XCT-01`).

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3 — las fixtures viven
aquí; `tests/conftest.py` sólo las importa y registra.

Las fixtures de IDENTIDAD y de PASES se REUTILIZAN de su módulo dueño
(`modules.salesianos_fest/tests/fixtures/`): no se duplican.
"""

from decimal import Decimal

import pytest

from modules.marketplace.domain.constants import (
    EstadoEntregaPedido,
    EstadoPedido,
    TipoItemPedido,
)
from modules.marketplace.domain.models import (
    CategoriaProducto,
    Pedido,
    PedidoDetalle,
    Producto,
)
from modules.validaciones.domain.constants import (
    OperacionValidacionChoices,
    TipoDerechoChoices,
)
from modules.validaciones.domain.models import Ticket

#: Las credenciales de la prueba. Son secretos de prueba: no sirven fuera.
CODIGO_TICKET_ENTRADA = "FEST-ENTRADA-0001"
CODIGO_TICKET_ENTREGA = "FEST-ENTREGA-0001"


# ── Credenciales ─────────────────────────────────────────────────────────────


@pytest.fixture
def ticket_entrada(db, beneficiario_pase):
    """La credencial que apunta a un derecho de ENTRADA."""
    return Ticket.objects.create(
        codigo=CODIGO_TICKET_ENTRADA,
        edicion_id=beneficiario_pase.edicion_id,
        tipo_derecho=TipoDerechoChoices.PASE,
        operacion=OperacionValidacionChoices.INGRESO,
        pase_beneficiario=beneficiario_pase,
    )


@pytest.fixture
def ticket_entrada_revocado(db, ticket_entrada):
    """La MISMA credencial, revocada por el operador."""
    from modules.validaciones.domain.constants import EstadoTicketChoices

    ticket_entrada.estado = EstadoTicketChoices.REVOCADO
    ticket_entrada.save(update_fields=["estado", "updated_at"])
    return ticket_entrada


# ── Tienda ───────────────────────────────────────────────────────────────────


@pytest.fixture
def categoria_producto(db, edicion_publicada):
    """La categoría del producto de la prueba."""
    return CategoriaProducto.objects.create(
        edicion=edicion_publicada,
        nombre="Merchandising",
        slug="merchandising",
        orden=1,
    )


@pytest.fixture
def producto(db, edicion_publicada, categoria_producto):
    """El producto que se entrega."""
    return Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Polo FEST",
        slug="polo-fest",
        precio=Decimal("35.00"),
        stock=10,
    )


@pytest.fixture
def pedido_pagado(db, edicion_publicada, persona, producto):
    """Un pedido PAGADO con su entrega PENDIENTE."""
    pedido = Pedido.objects.create(
        edicion=edicion_publicada,
        comprador=persona,
        estado=EstadoPedido.PAGADO,
        estado_entrega=EstadoEntregaPedido.PENDIENTE,
        total=Decimal("70.00"),
        moneda="PEN",
        token="token-pedido-xct01-no-usar-en-produccion",
        huella="huella-xct01",
        referencia="MARKETPLACE:XCT01:INICIAL",
    )
    PedidoDetalle.objects.create(
        pedido=pedido,
        tipo_concepto=TipoItemPedido.PRODUCTO,
        concepto_id=str(producto.id),
        concepto_nombre=producto.nombre,
        cantidad=2,
        precio_unitario=Decimal("35.00"),
        precio_aplicado=Decimal("35.00"),
    )
    return pedido


@pytest.fixture
def ticket_entrega(db, pedido_pagado):
    """La credencial que apunta a un pedido pagado."""
    return Ticket.objects.create(
        codigo=CODIGO_TICKET_ENTREGA,
        edicion_id=pedido_pagado.edicion_id,
        tipo_derecho=TipoDerechoChoices.PRODUCTO,
        operacion=OperacionValidacionChoices.ENTREGA,
        pedido=pedido_pagado,
    )


__all__ = [
    "CODIGO_TICKET_ENTRADA",
    "CODIGO_TICKET_ENTREGA",
    "categoria_producto",
    "pedido_pagado",
    "producto",
    "ticket_entrada",
    "ticket_entrada_revocado",
    "ticket_entrega",
]
