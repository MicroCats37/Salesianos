"""El snapshot de precio del pedido de marketplace (`DOM-05`).

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-PS-1.0.0`
Plan: `RN-C02` · `RN-C03` · `RN-C04` · `RN-M03` · `RN-M07` · `QA-M03` · `QA-M04`

GIVEN  el catálogo vigente y una intención de compra
WHEN   se crea el pedido y después cambian los precios
THEN   el detalle y el total CONGELADOS no cambian, y el pedido, el pago y la
       entrega siguen siendo TRES hechos distintos: **pagado NO es entregado**.

La prueba es de COMPORTAMIENTO: no mira la implementación, mira lo que el
dominio GARANTIZA — el precio que el comprador vio al pedir es el que el
pedido congeló, y el pago nunca habilita la entrega.
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import (
    EstadoEntregaPedido,
    EstadoPagoPedido,
    EstadoPedido,
)
from modules.marketplace.domain.models import Pedido, PedidoDetalle
from modules.marketplace.domain.schemas.pedido_schemas import (
    PedidoCreateData,
    PedidoItemCreateData,
)


def _intencion(producto_id, cantidad: int = 2) -> PedidoCreateData:
    """La intención de compra: QUÉ pide y CUÁNTO. NUNCA un importe."""
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
def test_el_alta_congela_el_precio_efectivo_del_catalogo(
    pedido_orchestrator, usuario_comprador, producto_con_oferta
):
    """GIVEN un producto con oferta vigente
    WHEN  se crea el pedido
    THEN  el detalle congela el PRECIO EFECTIVO y el total lo deriva el
          servidor: el cliente no impone ningún importe (RN-C02, RN-M03).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto_con_oferta.id, cantidad=2),
    )

    assert resultado.total == Decimal("14.00")  # 7.00 (oferta) x 2
    assert [linea.precio_aplicado for linea in resultado.lineas] == [
        Decimal("7.00")
    ]
    assert [linea.precio_unitario for linea in resultado.lineas] == [
        Decimal("10.00")
    ]

    detalle = PedidoDetalle.objects.get(pedido_id=resultado.id)
    assert detalle.precio_unitario == Decimal("10.00")
    assert detalle.precio_aplicado == Decimal("7.00")
    assert detalle.subtotal == Decimal("14.00")


@pytest.mark.django_db
def test_un_cambio_de_precio_posterior_no_altera_el_pedido(
    pedido_orchestrator, usuario_comprador, producto_con_oferta
):
    """GIVEN un pedido ya creado
    WHEN  el catálogo cambia de precio (y la oferta caduca)
    THEN  el detalle y el total del pedido NO cambian: el histórico no cambia
          por una oferta nueva (RN-M03 · `QA-M03`).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto_con_oferta.id, cantidad=2),
    )
    assert resultado.total == Decimal("14.00")

    producto_con_oferta.precio = Decimal("20.00")
    producto_con_oferta.precio_oferta = None
    producto_con_oferta.oferta_inicia = None
    producto_con_oferta.oferta_termina = None
    producto_con_oferta.save()

    seguimiento = async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )

    assert seguimiento.total == Decimal("14.00")
    assert [linea.precio_aplicado for linea in seguimiento.lineas] == [
        Decimal("7.00")
    ]
    assert [linea.precio_unitario for linea in seguimiento.lineas] == [
        Decimal("10.00")
    ]

    detalle = PedidoDetalle.objects.get(pedido_id=resultado.id)
    assert detalle.precio_aplicado == Decimal("7.00")
    assert detalle.precio_unitario == Decimal("10.00")


@pytest.mark.django_db
def test_el_pedido_pendiente_tiene_los_tres_estados_por_separado(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido recién creado
    THEN  `estado`, `estado_pago` y `estado_entrega` son PENDIENTE: el pago y
          la entrega NO están resueltos al crearse (RN-M07).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto.id),
    )

    assert resultado.estado == EstadoPedido.PENDIENTE
    assert resultado.estado_pago == EstadoPagoPedido.PENDIENTE
    assert resultado.estado_entrega == EstadoEntregaPedido.PENDIENTE
    assert resultado.siguientes_acciones == ["REALIZAR_PAGO"]


@pytest.mark.django_db
def test_el_pago_confirmado_paga_el_pedido_pero_no_lo_entrega(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido cuya compra queda pagada
    WHEN  se consulta el pedido
    THEN  el PEDIDO pasa a `PAGADO` y el PAGO a `CONFIRMADO`, pero la ENTREGA
          sigue `PENDIENTE`: **pagado NO es entregado** (RN-M07 · `QA-M04`).
    """
    from modules.commerce.domain.constants import EstadoCompra

    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto.id),
    )

    pedido = Pedido.objects.get(id=resultado.id)
    compra = pedido.compra
    assert compra is not None
    compra.estado = EstadoCompra.PAGADA
    compra.save(update_fields=["estado"])

    seguimiento = async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )

    assert seguimiento.estado == EstadoPedido.PAGADO
    assert seguimiento.estado_pago == EstadoPagoPedido.CONFIRMADO
    assert seguimiento.estado_entrega == EstadoEntregaPedido.PENDIENTE
    assert seguimiento.siguientes_acciones == ["ESPERAR_ENTREGA"]

    pedido.refresh_from_db()
    assert pedido.estado == EstadoPedido.PAGADO
    assert pedido.estado_entrega == EstadoEntregaPedido.PENDIENTE


@pytest.mark.django_db
def test_la_compra_cancelada_cancela_el_pedido_sin_tocar_la_entrega(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido cuya compra queda cancelada
    THEN  el pedido pasa a `CANCELADO` y la acción segura es reintentar
          (RN-C07). La entrega tampoco se mueve: la mueve `DOM-06`.
    """
    from modules.commerce.domain.constants import EstadoCompra

    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto.id),
    )

    pedido = Pedido.objects.get(id=resultado.id)
    compra = pedido.compra
    compra.estado = EstadoCompra.CANCELADA
    compra.save(update_fields=["estado"])

    seguimiento = async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )

    assert seguimiento.estado == EstadoPedido.CANCELADO
    assert seguimiento.estado_pago == EstadoPagoPedido.NO_COMPLETADO
    assert seguimiento.estado_entrega == EstadoEntregaPedido.PENDIENTE
    assert seguimiento.siguientes_acciones == ["REINTENTAR_COMPRA"]


@pytest.mark.django_db
def test_el_snapshot_de_la_compra_es_el_mismo_del_pedido(
    pedido_orchestrator, usuario_comprador, producto_con_oferta
):
    """GIVEN un pedido creado
    THEN  la compra que lo financia guarda el MISMO snapshot congelado: el
          pedido y la compra dicen lo mismo (RN-C01, RN-M03).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(producto_con_oferta.id, cantidad=3),
    )

    pedido = Pedido.objects.get(id=resultado.id)
    compra = pedido.compra

    assert compra.total == Decimal("21.00")
    assert compra.origen == "MARKETPLACE"
    assert len(compra.lineas_snapshot) == 1
    linea = compra.lineas_snapshot[0]
    assert linea["precio_aplicado"] == "7.00"
    assert linea["cantidad"] == 3
    assert linea["concepto_id"] == str(producto_con_oferta.id)
