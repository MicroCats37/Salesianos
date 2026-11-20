"""La bitácora de inventario: movimientos manuales y reversas (`DOM-06`).

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0`
Plan: `RN-M04` · `RN-M05` · `QA-M02` · `FL-09`

GIVEN  un producto con existencias
WHEN   un administrador registra una salida, un ajuste o una reversa
THEN   queda un MOVIMIENTO con producto, signo/cantidad, motivo, referencia de
       origen y actor — y NUNCA una compra ni un pago ficticios (RN-M04 ·
       RN-M05 · `QA-M02`).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import TipoMovimientoInventario
from modules.marketplace.domain.exceptions import (
    MovimientoInventarioInvalidoError,
    MovimientoInmutableError,
    StockInsuficienteError,
)
from modules.marketplace.domain.models import MovimientoInventario
from modules.marketplace.domain.schemas.inventario_schemas import (
    RegistrarMovimientoInventarioData,
    RevertirMovimientoInventarioData,
)


@pytest.mark.django_db
def test_una_salida_sin_venta_no_crea_compra_ni_pago(
    inventario_orchestrator, usuario_admin, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  un administrador registra una MERMA de 5 unidades
    THEN  el stock baja a 5 y NO existe ninguna compra ni ningún pago: una
          salida sin venta no es una compra ficticia (RN-M05 · `QA-M02`).
    """
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago

    resultado = async_to_sync(inventario_orchestrator.registrar_movimiento)(
        usuario_admin,
        RegistrarMovimientoInventarioData(
            producto_id=str(producto_con_stock.id),
            tipo=TipoMovimientoInventario.MERMA,
            cantidad=-5,
            motivo="Merma por rotura en el almacén",
        ),
    )

    assert resultado.cantidad == -5
    assert resultado.tipo == TipoMovimientoInventario.MERMA
    assert resultado.motivo == "Merma por rotura en el almacén"
    assert resultado.actor_id is not None
    assert resultado.referencia

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 5
    assert producto_con_stock.disponible == 5

    assert Compra.objects.count() == 0
    assert OrdenPago.objects.count() == 0


@pytest.mark.django_db
def test_el_movimiento_es_inmutable(
    inventario_orchestrator, usuario_admin, producto_con_stock
):
    """GIVEN un movimiento ya registrado
    WHEN  se intenta editarlo o borrarlo
    THEN  se rechaza: la bitácora no se toca; una corrección es una REVERSA
          (RN-M04).
    """
    async_to_sync(inventario_orchestrator.registrar_movimiento)(
        usuario_admin,
        RegistrarMovimientoInventarioData(
            producto_id=str(producto_con_stock.id),
            tipo=TipoMovimientoInventario.CONSUMO_INTERNO,
            cantidad=-2,
            motivo="Consumo interno del stand",
        ),
    )
    movimiento = MovimientoInventario.objects.get()

    movimiento.cantidad = -99
    with pytest.raises(MovimientoInmutableError):
        movimiento.save()

    with pytest.raises(MovimientoInmutableError):
        movimiento.delete()


@pytest.mark.django_db
def test_la_reversa_compensa_el_movimiento_original(
    inventario_orchestrator, usuario_admin, producto_con_stock
):
    """GIVEN una reposición de 8 unidades
    WHEN  se compensa con una reversa
    THEN  aparece un SEGUNDO movimiento de signo contrario, ligado al
          original, y el stock vuelve al punto de partida (RN-M04).
    """
    original = async_to_sync(inventario_orchestrator.registrar_movimiento)(
        usuario_admin,
        RegistrarMovimientoInventarioData(
            producto_id=str(producto_con_stock.id),
            tipo=TipoMovimientoInventario.REPOSICION,
            cantidad=8,
            motivo="Recepción de mercadería",
        ),
    )

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 18

    reversa = async_to_sync(inventario_orchestrator.revertir_movimiento)(
        usuario_admin,
        RevertirMovimientoInventarioData(
            movimiento_id=str(original.id),
            motivo="Recepción duplicada por error de conteo",
        ),
    )

    assert reversa.cantidad == -8
    assert reversa.tipo == TipoMovimientoInventario.REVERSION

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10

    movimientos = list(MovimientoInventario.objects.order_by("created_at", "id"))
    assert len(movimientos) == 2
    assert movimientos[1].compensatorio_id == movimientos[0].id
    assert movimientos[0].cantidad == 8
    assert movimientos[1].cantidad == -8


@pytest.mark.django_db
def test_un_movimiento_con_el_signo_incoherente_es_rechazado(
    inventario_orchestrator, usuario_admin, producto_con_stock
):
    """GIVEN una naturaleza que impone el signo (una reposición ENTRA)
    WHEN  se declara con el signo contrario
    THEN  se rechaza con `MOVIMIENTO_INVENTARIO_INVALIDO` (422) y no se
          escribe nada (RN-M04).
    """
    with pytest.raises(MovimientoInventarioInvalidoError):
        async_to_sync(inventario_orchestrator.registrar_movimiento)(
            usuario_admin,
            RegistrarMovimientoInventarioData(
                producto_id=str(producto_con_stock.id),
                tipo=TipoMovimientoInventario.REPOSICION,
                cantidad=-8,
                motivo="Entrada con signo invertido",
            ),
        )

    assert MovimientoInventario.objects.count() == 0
    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10


@pytest.mark.django_db
def test_una_salida_mayor_que_el_stock_es_rechazada(
    inventario_orchestrator, usuario_admin, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  se registra una salida de 20 unidades
    THEN  se rechaza con `STOCK_INSUFICIENTE` (409) y el stock no cambia.
    """
    with pytest.raises(StockInsuficienteError):
        async_to_sync(inventario_orchestrator.registrar_movimiento)(
            usuario_admin,
            RegistrarMovimientoInventarioData(
                producto_id=str(producto_con_stock.id),
                tipo=TipoMovimientoInventario.SALIDA_SIN_VENTA,
                cantidad=-20,
                motivo="Regalo a la organización del evento",
            ),
        )

    assert MovimientoInventario.objects.count() == 0
    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10
