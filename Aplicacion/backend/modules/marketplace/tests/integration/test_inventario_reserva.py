"""La reserva de existencias y la anti-sobreventa (`DOM-06`).

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0`
Plan: `RN-M06` · `PD-05` · `QA-M01` · `FL-08` §3

GIVEN  un producto con existencias declaradas
WHEN   se crean pedidos pendientes
THEN   cada pedido APARTA sus unidades, el catálogo calcula lo DISPONIBLE y
       un pedido que no alcanza NO se crea (RN-M06 · `QA-M01`).

**LA ESTRATEGIA (RN-M06, `PD-05` DECIDIDO).** El stock es POR EDICIÓN (el
inventario vive en el producto, y el producto pertenece a una edición). La
reserva es la unidad que sostiene la anti-sobreventa: mientras un pedido
está pendiente, sus unidades están apartadas.

La carrera simultánea REAL se verifica en la fase de verificación (VER-*),
como en `DOM-05`: aquí se comprueba la MISMA GARANTÍA de forma determinista
— el segundo pedido se rechaza porque las unidades ya están reservadas.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import (
    EstadoPedido,
    EstadoReservaInventario,
)
from modules.marketplace.domain.exceptions import StockInsuficienteError
from modules.marketplace.domain.models import Pedido, Producto, ReservaInventario
from modules.marketplace.domain.schemas.pedido_schemas import (
    PedidoCreateData,
    PedidoItemCreateData,
)


def _intencion(producto_id, cantidad: int = 1) -> PedidoCreateData:
    """La intención de compra: QUÉ pide y CUÁNTO."""
    return PedidoCreateData(
        items=[
            PedidoItemCreateData(
                tipo="PRODUCTO",
                producto_id=producto_id,
                cantidad=cantidad,
            )
        ]
    )


@pytest.mark.django_db
def test_el_pedido_pendiente_aparta_sus_unidades(
    pedido_orchestrator, usuario_comprador, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  se crea un pedido de 3 unidades
    THEN  el producto queda con 3 RESERVADAS y 7 DISPONIBLES: lo reservado
          no se puede vender dos veces (RN-M06).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto_con_stock.id, cantidad=3),
    )

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10
    assert producto_con_stock.reservado == 3
    assert producto_con_stock.disponible == 7

    reserva = ReservaInventario.objects.get(pedido_id=resultado.id)
    assert reserva.cantidad == 3
    assert reserva.estado == EstadoReservaInventario.ACTIVA
    assert reserva.referencia == f"PEDIDO:{resultado.id}:{producto_con_stock.id}"


@pytest.mark.django_db
def test_un_producto_sin_existencias_no_se_puede_pedir(
    pedido_orchestrator, usuario_comprador, producto_agotado
):
    """GIVEN un producto AGOTADO (`stock = 0`)
    WHEN  se intenta crear un pedido
    THEN  se rechaza con `STOCK_INSUFICIENTE` (409) y NO queda ningún pedido
          ni ninguna reserva (RN-M06).
    """
    with pytest.raises(StockInsuficienteError):
        async_to_sync(pedido_orchestrator.crear_pedido)(
            usuario_comprador,
            _intencion(producto_agotado.id),
        )

    assert Pedido.objects.count() == 0
    assert ReservaInventario.objects.count() == 0
    assert Producto.objects.get(id=producto_agotado.id).reservado == 0


@pytest.mark.django_db
def test_un_pedido_que_excede_el_stock_no_se_crea(
    pedido_orchestrator, usuario_comprador, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  se piden 11 unidades
    THEN  se rechaza con `STOCK_INSUFICIENTE` y NO queda el pedido a medias:
          la reserva vive en la misma transacción que el alta (RN-M06).
    """
    with pytest.raises(StockInsuficienteError):
        async_to_sync(pedido_orchestrator.crear_pedido)(
            usuario_comprador,
            _intencion(producto_con_stock.id, cantidad=11),
        )

    assert Pedido.objects.count() == 0
    assert ReservaInventario.objects.count() == 0
    assert Producto.objects.get(id=producto_con_stock.id).reservado == 0


@pytest.mark.django_db
def test_dos_pedidos_pendientes_no_sobrevenden(
    pedido_orchestrator, usuario_comprador, usuario_ajeno, edicion_publicada, categoria_producto
):
    """GIVEN un producto con UNA sola unidad
    WHEN  dos compradores distintos piden esa unidad
    THEN  el primero la reserva y el SEGUNDO recibe `STOCK_INSUFICIENTE`: un
          pedido pendiente no vende más de lo disponible (`QA-M01`).
    """
    from modules.marketplace.domain.models import Producto

    producto = Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Última camiseta",
        slug="ultima-camiseta",
        precio="15.00",
        estado="ACTIVO",
        stock=1,
    )

    primero = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto.id),
    )
    assert primero.estado == EstadoPedido.PENDIENTE

    with pytest.raises(StockInsuficienteError):
        async_to_sync(pedido_orchestrator.crear_pedido)(
            usuario_ajeno,
            _intencion(producto.id),
        )

    producto.refresh_from_db()
    assert producto.stock == 1
    assert producto.reservado == 1
    assert producto.disponible == 0
    assert ReservaInventario.objects.count() == 1
    assert Pedido.objects.count() == 1


@pytest.mark.django_db
def test_la_reserva_se_libera_al_cancelar_el_pedido(
    pedido_orchestrator, usuario_comprador, producto_con_stock
):
    """GIVEN un pedido pendiente que reserva 2 unidades
    WHEN  su compra se cancela
    THEN  el pedido queda `CANCELADO`, la reserva `LIBERADA` y las unidades
          vuelven al catálogo (RN-M06).
    """
    from modules.commerce.domain.constants import EstadoCompra

    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto_con_stock.id, cantidad=2),
    )
    producto_con_stock.refresh_from_db()
    assert producto_con_stock.reservado == 2

    pedido = Pedido.objects.get(id=resultado.id)
    compra = pedido.compra
    compra.estado = EstadoCompra.CANCELADA
    compra.save(update_fields=["estado"])

    async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )

    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.CANCELADO
    assert pedido.estado_entrega == "PENDIENTE"

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.reservado == 0
    assert producto_con_stock.disponible == 10

    reserva = ReservaInventario.objects.get(pedido_id=resultado.id)
    assert reserva.estado == EstadoReservaInventario.LIBERADA
