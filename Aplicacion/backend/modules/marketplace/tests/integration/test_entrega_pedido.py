"""La entrega del pedido: un hecho POSTERIOR, auditable y reintentable.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0`
Plan: `RN-M07` · `QA-M04` · `FL-08` §5

GIVEN  un pedido pagado
WHEN   un operador confirma la entrega
THEN   el estado de la ENTREGA avanza a `ENTREGADO` y queda un ACTA con su
       actor y sus cantidades — sin tocar el estado del pedido ni el del
       pago, y sin mover el stock otra vez (RN-M07 · `QA-M04`).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import (
    EstadoEntregaPedido,
    EstadoPedido,
)
from modules.marketplace.domain.exceptions import (
    PedidoNoPagadoError,
)
from modules.marketplace.domain.models import EntregaPedido, Pedido
from modules.marketplace.domain.schemas.pedido_schemas import (
    PedidoCreateData,
    PedidoItemCreateData,
)


@pytest.mark.django_db
def test_la_entrega_mueve_solo_el_estado_de_entrega(
    pedido_orchestrator, usuario_admin, pedido_pagado, producto_con_stock
):
    """GIVEN un pedido PAGADO
    WHEN  el operador confirma la entrega
    THEN  la entrega queda `ENTREGADO` y NI el pedido NI el pago cambian:
          son TRES hechos separados (RN-M07 · `QA-M04`).
    """
    resultado = async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )

    assert resultado.estado_entrega == EstadoEntregaPedido.ENTREGADO
    assert resultado.cantidad_total == 1
    assert resultado.actor_id is not None

    pedido_pagado.refresh_from_db()
    assert pedido_pagado.estado == EstadoPedido.PAGADO
    assert pedido_pagado.estado_entrega == EstadoEntregaPedido.ENTREGADO


@pytest.mark.django_db
def test_no_se_entrega_un_pedido_no_pagado(
    pedido_orchestrator, usuario_comprador, usuario_admin, producto_con_stock
):
    """GIVEN un pedido PENDIENTE de pago
    WHEN  el operador intenta confirmar la entrega
    THEN  se rechaza con `PEDIDO_NO_PAGADO` (409): entregado SÍ exige
          pagado, pero pagado NO habilita la entrega (RN-M07).
    """
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
            numero_documento="10000002",
            nombres="Comprador",
            apellidos="Pendiente",
        ),
    )

    with pytest.raises(PedidoNoPagadoError):
        async_to_sync(pedido_orchestrator.confirmar_entrega)(
            usuario_admin,
            str(resultado.id),
        )

    assert EntregaPedido.objects.count() == 0
    pedido = Pedido.objects.get(id=resultado.id)
    assert pedido.estado_entrega == EstadoEntregaPedido.PENDIENTE


@pytest.mark.django_db
def test_la_entrega_es_idempotente_y_reintentable(
    pedido_orchestrator, usuario_admin, pedido_pagado
):
    """GIVEN un pedido ya entregado
    WHEN  el operador REINTENTA la confirmación
    THEN  se devuelve el MISMO acta: la entrega no se duplica y el reintento
          es seguro (QA-M04 · `FL-10` §4).
    """
    primera = async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )
    segunda = async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )

    assert primera.pedido_id == segunda.pedido_id
    assert primera.cantidad_total == segunda.cantidad_total
    assert primera.entregada_en == segunda.entregada_en

    assert EntregaPedido.objects.count() == 1


@pytest.mark.django_db
def test_el_acta_registra_el_actor_y_las_cantidades(
    pedido_orchestrator, usuario_admin, pedido_pagado, producto_con_stock
):
    """GIVEN un pedido pagado de 1 unidad
    WHEN  se confirma la entrega
    THEN  el acta guarda el ACTOR, la cantidad y el detalle de lo entregado:
          la entrega es auditable e independiente (QA-M04).
    """
    async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )

    entrega = EntregaPedido.objects.get(pedido=pedido_pagado)
    assert entrega.actor_id == usuario_admin.id
    assert entrega.cantidad_total == 1
    assert entrega.referencia == f"PEDIDO:{pedido_pagado.id}:ENTREGA"
    assert len(entrega.detalle) == 1
    assert entrega.detalle[0]["concepto_id"] == str(producto_con_stock.id)
    assert entrega.detalle[0]["cantidad"] == 1


@pytest.mark.django_db
def test_la_entrega_no_vuelve_a_mover_el_stock(
    pedido_orchestrator, usuario_admin, pedido_pagado, producto_con_stock
):
    """GIVEN un pedido pagado (el stock ya salió al venderse)
    WHEN  se confirma la entrega
    THEN  el stock NO cambia: la entrega no es una segunda salida
          (RN-M04 · RN-M07).
    """
    producto_con_stock.refresh_from_db()
    stock_antes = producto_con_stock.stock

    async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == stock_antes


@pytest.mark.django_db
def test_el_listado_separa_recogidas_pendientes_y_entregadas(
    inventario_orchestrator,
    pedido_orchestrator,
    usuario_admin,
    pedido_pagado,
):
    """La tienda ve ambas colas con el nombre y apellido del comprador."""
    async_to_sync(pedido_orchestrator.confirmar_entrega)(
        usuario_admin,
        str(pedido_pagado.id),
    )

    resultado = async_to_sync(inventario_orchestrator.listar_entregas)()

    assert resultado.pendientes == []
    assert len(resultado.entregadas) == 1
    assert resultado.entregadas[0].pedido_id == pedido_pagado.id
    assert resultado.entregadas[0].comprador_nombres == pedido_pagado.comprador.nombres
    assert resultado.entregadas[0].comprador_apellidos == pedido_pagado.comprador.apellidos
    assert resultado.entregadas[0].comprador_documento == pedido_pagado.comprador.numero_documento
