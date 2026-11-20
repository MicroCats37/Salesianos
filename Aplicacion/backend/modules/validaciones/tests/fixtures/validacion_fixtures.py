"""Fixtures del módulo de VALIDACIONES (`XCT-01`).

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3 — las fixtures viven
aquí; `tests/conftest.py` sólo las importa y registra.

Las fixtures de IDENTIDAD y de PASES se REUTILIZAN de su módulo dueño
(`modules.salesianos_fest/tests/fixtures/`): no se duplican.
"""

from decimal import Decimal

import pytest
from asgiref.sync import sync_to_async

from modules.marketplace.domain.constants import (
    EstadoEntregaPedido,
    EstadoPedido,
    TipoItemPedido,
)
from modules.marketplace.domain.models import (
    CategoriaProducto,
    EntregaPedido,
    Pedido,
    PedidoDetalle,
    Producto,
)
from modules.validaciones.domain.constants import (
    OperacionValidacionChoices,
    TipoDerechoChoices,
)
from modules.validaciones.domain.models import Ticket, ValidacionTicket

#: Las credenciales de la prueba. Son secretos de prueba: no sirven fuera.
CODIGO_TICKET_ENTRADA = "FEST-ENTRADA-0001"
CODIGO_TICKET_ENTREGA = "FEST-ENTREGA-0001"


# ── Lecturas del acta desde un contexto async ───────────────────────────────
#
# Django prohíbe el ORM síncrono dentro de un contexto async: estas lecturas
# van por `sync_to_async` (el patrón del módulo `usuarios`).


def _contar_actas(**filtros) -> int:
    return ValidacionTicket.objects.filter(**filtros).count()


def _listar_actas(**filtros) -> list:
    return list(ValidacionTicket.objects.filter(**filtros))


def _primera_acta(**filtros):
    return _listar_actas(**filtros)[0] if _listar_actas(**filtros) else None


def _consumido_de(ticket) -> int:
    """La cantidad consumida del derecho al que apunta la credencial."""
    beneficio = ticket.pase_beneficiario
    beneficio.refresh_from_db()
    return beneficio.cantidad_consumida


def _revocar(beneficiario, estado: str) -> None:
    """Cambia el estado del derecho y lo persiste."""
    beneficiario.estado = estado
    beneficiario.save(update_fields=["estado", "updated_at"])


async def contar_actas(**filtros) -> int:
    """Las actas del acta con esos filtros."""
    return await sync_to_async(_contar_actas)(**filtros)


async def listar_actas(**filtros) -> list:
    """Las actas con esos filtros."""
    return await sync_to_async(_listar_actas)(**filtros)


async def primera_acta(**filtros):
    """La primera acta con esos filtros, o `None`."""
    return await sync_to_async(_primera_acta)(**filtros)


async def consumido_de(ticket) -> int:
    """La cantidad consumida del derecho de la credencial."""
    return await sync_to_async(_consumido_de)(ticket)


async def revocar(beneficiario, estado: str) -> None:
    """Cambia el estado del derecho desde un contexto async."""
    await sync_to_async(_revocar)(beneficiario, estado)


def _estado_entrega_de(pedido) -> str:
    pedido.refresh_from_db()
    return pedido.estado_entrega


def _contar_entregas_de(pedido) -> int:
    return EntregaPedido.objects.filter(pedido=pedido).count()


def _cambiar_estado_pedido(pedido, estado: str) -> None:
    pedido.estado = estado
    pedido.save(update_fields=["estado", "updated_at"])


async def estado_entrega_de(pedido) -> str:
    """El estado de entrega del pedido, leído desde un contexto async."""
    return await sync_to_async(_estado_entrega_de)(pedido)


async def contar_entregas_de(pedido) -> int:
    """Las entregas registradas del pedido, contadas desde un contexto async."""
    return await sync_to_async(_contar_entregas_de)(pedido)


async def cambiar_estado_pedido(pedido, estado: str) -> None:
    """Cambia el estado del pedido desde un contexto async."""
    await sync_to_async(_cambiar_estado_pedido)(pedido, estado)


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
    "cambiar_estado_pedido",
    "categoria_producto",
    "consumido_de",
    "contar_actas",
    "contar_entregas_de",
    "estado_entrega_de",
    "listar_actas",
    "pedido_pagado",
    "primera_acta",
    "producto",
    "revocar",
    "ticket_entrada",
    "ticket_entrada_revocado",
    "ticket_entrega",
]
