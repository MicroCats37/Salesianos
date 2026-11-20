"""El efecto de stock de un pago confirmado: EXACTAMENTE una vez (`DOM-06`).

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, I-2, I-3)
Plan: `RN-M06` · `FR-04` I-3

GIVEN  un pedido pendiente cuya compra queda pagada
WHEN   `commerce` despacha la activación del origen `MARKETPLACE`
THEN   el stock FÍSICO sale del producto, la reserva se CONFIRMA y queda UN
       movimiento de venta: un webhook repetido NO descuenta dos veces.

**LA FRONTERA.** El activador implementa el puerto CONGELADO de `commerce`
(`IActivadorDominioCompra`): este paquete CONSUME el puerto y no edita los
interiores de `commerce` ni de `pagos`.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import (
    EstadoReservaInventario,
    TipoMovimientoInventario,
)
from modules.marketplace.domain.models import (
    MovimientoInventario,
    Pedido,
    ReservaInventario,
)
from modules.marketplace.domain.services.core.activador_marketplace import (
    ActivadorMarketplace,
)


def _contexto_de(pedido):
    """El contexto de activación que `commerce` entrega al dominio."""
    from modules.commerce.domain.constants import OrigenCompra
    from modules.commerce.domain.schemas.compra_schemas import (
        ContextoActivacionCompra,
    )

    compra = pedido.compra
    return ContextoActivacionCompra(
        compra_id=compra.id,
        origen=OrigenCompra.MARKETPLACE,
        clave=f"activacion:{OrigenCompra.MARKETPLACE}:{compra.id}",
        persona_id=compra.persona_id,
        referencia=compra.referencia,
        total=compra.total,
        moneda=compra.moneda,
        lineas_snapshot=compra.lineas_snapshot,
    )


@pytest.mark.django_db
def test_el_modulo_registra_su_activador_para_el_origen_marketplace():
    """GIVEN el módulo `marketplace` arrancado
    THEN  el registro de activadores de `commerce` tiene un activador para el
          origen `MARKETPLACE`: un pago confirmado llega al stock (FR-04 §2.3).
    """
    from modules.commerce.domain.constants import OrigenCompra
    from modules.commerce.domain.services.core.registro_activadores_compra import (
        obtener_registro,
    )

    activador = obtener_registro().resolver(OrigenCompra.MARKETPLACE)
    assert activador is not None
    assert isinstance(activador, ActivadorMarketplace)


@pytest.mark.django_db
def test_la_activacion_confirma_el_stock_una_sola_vez(
    pedido_orchestrator, usuario_comprador, producto_con_stock
):
    """GIVEN un pedido pendiente que reservó 1 unidad
    WHEN  el pago se confirma y el dominio se activa
    THEN  el stock físico baja, la reserva queda `CONFIRMADA` y queda UN
          movimiento de venta (RN-M06).
    """
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
            ]
        ),
    )
    pedido = Pedido.objects.get(id=resultado.id)

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10
    assert producto_con_stock.reservado == 1

    activacion = ActivadorMarketplace().activar(_contexto_de(pedido))
    assert activacion.exito is True
    assert activacion.codigo == "STOCK_CONFIRMADO"
    assert activacion.detalle["cantidad"] == 1

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 9
    assert producto_con_stock.reservado == 0
    assert producto_con_stock.disponible == 9

    reserva = ReservaInventario.objects.get(pedido_id=pedido.id)
    assert reserva.estado == EstadoReservaInventario.CONFIRMADA

    movimiento = MovimientoInventario.objects.get()
    assert movimiento.tipo == TipoMovimientoInventario.VENTA
    assert movimiento.cantidad == -1
    assert movimiento.referencia == f"PEDIDO:{pedido.id}:{producto_con_stock.id}"
    assert movimiento.actor_id is None


@pytest.mark.django_db
def test_una_activacion_repetida_no_descuenta_dos_veces(
    pedido_orchestrator, usuario_comprador, producto_con_stock
):
    """GIVEN un pedido pendiente cuya venta ya se activó
    WHEN  llega OTRA activación (un webhook repetido)
    THEN  no se vuelve a descontar el stock ni a crear un movimiento
          (FR-04 I-2 · I-3 · RN-M06).
    """
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
                    cantidad=2,
                )
            ]
        ),
    )
    pedido = Pedido.objects.get(id=resultado.id)
    contexto = _contexto_de(pedido)

    activador = ActivadorMarketplace()
    primera = activador.activar(contexto)
    segunda = activador.activar(contexto)

    assert primera.exito is True
    assert segunda.exito is True
    assert segunda.codigo == "STOCK_YA_CONFIRMADO"
    assert segunda.detalle["cantidad"] == 0

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 8
    assert producto_con_stock.reservado == 0

    assert MovimientoInventario.objects.count() == 1
