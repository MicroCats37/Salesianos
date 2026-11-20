"""Fixtures del inventario, la reserva y la entrega (`DOM-06`).

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures viven aquí; `modules/marketplace/tests/conftest.py` sólo las
importa y registra. No hay mocks: los dobles son implementaciones reales de
los puertos y los servicios son los de producción.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.models import Producto


@pytest.fixture
def producto_con_stock(db, edicion_publicada, categoria_producto):
    """Producto con existencias declaradas: `stock = 10`."""
    return Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Camiseta del festival",
        slug="camiseta-festival",
        descripcion="Camiseta oficial.",
        precio="15.00",
        estado="ACTIVO",
        stock=10,
    )


@pytest.fixture
def producto_agotado(db, edicion_publicada, categoria_producto):
    """Producto SIN existencias: está AGOTADO (RN-M06)."""
    return Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Última unidad",
        slug="ultima-unidad",
        precio="9.00",
        estado="ACTIVO",
        stock=0,
    )


@pytest.fixture
def inventario_orchestrator(db):
    """El orquestador del inventario, resuelto por el INYECTOR de producción.

    Es el MISMO wiring que usa la HTTP: `MarketplaceModule` registra los
    puertos y sus adaptadores. Resolverlo por el inyector verifica el DI, no
    sólo el comportamiento.
    """
    from ninja_extra.dependency_resolver import service_resolver

    from modules.marketplace.domain.services.orchestrators.inventario_orchestrator import (
        InventarioOrchestrator,
    )

    return service_resolver(InventarioOrchestrator)


@pytest.fixture
def pedido_pagado(db, pedido_orchestrator, usuario_comprador, producto_con_stock):
    """Un pedido PAGADO cuya entrega sigue PENDIENTE (RN-M07 · `QA-M04`).

    El pago se simula marcando la COMPRA como pagada (el mismo camino que
    usa `DOM-05`) y reconciliando el pedido: la entrega NO se habilita.
    """
    from modules.commerce.domain.constants import EstadoCompra

    from modules.marketplace.domain.models import Pedido
    from modules.marketplace.domain.schemas.pedido_schemas import (
        PedidoCreateData,
        PedidoItemCreateData,
    )

    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        PedidoCreateData(
            items=[
                PedidoItemCreateData(
                    tipo="PRODUCTO",
                    producto_id=producto_con_stock.id,
                    cantidad=1,
                )
            ],
            tipo_documento="DNI",
            numero_documento="10000001",
            nombres="Comprador",
            apellidos="De Prueba",
        ),
    )
    pedido = Pedido.objects.get(id=resultado.id)
    compra = pedido.compra
    compra.estado = EstadoCompra.PAGADA
    compra.save(update_fields=["estado"])

    # La reconciliación mueve el PEDIDO a `PAGADO`; la ENTREGA sigue
    # `PENDIENTE` (RN-M07).
    async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )
    pedido.refresh_from_db()
    return pedido


__all__ = [
    "inventario_orchestrator",
    "pedido_pagado",
    "producto_agotado",
    "producto_con_stock",
]
