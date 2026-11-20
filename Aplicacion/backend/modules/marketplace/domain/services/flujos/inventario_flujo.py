"""`InventarioFlujo` — los casos de uso de escritura del inventario.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.4

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`
para las escrituras administrativas del inventario (P5).

**UNA SALIDA SIN VENTA NO ES UNA COMPRA (RN-M05 · `QA-M02`).** Ninguno de
estos caminos crea `Compra`, `OrdenPago` ni `Pedido`: el movimiento de
inventario es el ÚNICO hecho que deja la operación.
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.marketplace.domain.exceptions import (
    MovimientoInventarioNoEncontradoError,
    ProductoNoEncontradoError,
)
from modules.marketplace.domain.schemas.inventario_schemas import (
    RegistrarMovimientoInventarioData,
    RevertirMovimientoInventarioData,
)
from modules.marketplace.domain.selectors.inventario_selector import InventarioSelector
from modules.marketplace.domain.services.core.inventario_core_service import (
    InventarioCoreService,
)


class InventarioFlujo:
    """Casos de uso de escritura del inventario de marketplace."""

    @inject
    def __init__(
        self,
        core_service: InventarioCoreService,
        selector: InventarioSelector,
    ):
        self.core_service = core_service
        self.selector = selector

    # ── Movimiento manual (FL-09) ───────────────────────────────────────────

    async def registrar_movimiento(
        self,
        edicion_id,
        data: RegistrarMovimientoInventarioData,
        actor,
    ):
        """Registra una entrada, una salida o un ajuste, con motivo y actor.

        El alcance lo resuelve el servidor: el producto tiene que pertenecer
        a la edición vigente (`RN-E01`).
        """
        return await sync_to_async(self._registrar_movimiento_sync)(
            edicion_id, data, actor
        )

    @transaction.atomic()
    def _registrar_movimiento_sync(self, edicion_id, data, actor):
        """Registro atómico del movimiento y del ajuste del stock."""
        producto = self._producto_del_alcance(edicion_id, data.producto_id)
        movimiento = self.core_service.registrar_movimiento(
            producto,
            data.tipo,
            data.cantidad,
            data.motivo,
            actor,
        )
        return self.core_service.result_movimiento(movimiento)

    # ── Reversa compensatoria (RN-M04) ──────────────────────────────────────

    async def revertir_movimiento(
        self,
        edicion_id,
        data: RevertirMovimientoInventarioData,
        actor,
    ):
        """Compensa un movimiento ya registrado con otro de signo contrario.

        El movimiento original NO se edita ni se borra: queda la traza.
        """
        return await sync_to_async(self._revertir_movimiento_sync)(
            edicion_id, data, actor
        )

    @transaction.atomic()
    def _revertir_movimiento_sync(self, edicion_id, data, actor):
        """Reversa atómica del movimiento y del ajuste del stock."""
        movimiento = self.selector.obtener_movimiento(data.movimiento_id)
        if movimiento is None:
            raise MovimientoInventarioNoEncontradoError()
        producto = self._producto_del_alcance(edicion_id, movimiento.producto_id)
        reversa = self.core_service.revertir_movimiento(
            movimiento, actor, data.motivo
        )
        return self.core_service.result_movimiento(reversa)

    # ── Internos ─────────────────────────────────────────────────────────────

    @staticmethod
    def _producto_del_alcance(edicion_id, producto_id):
        """El producto, si pertenece a la edición; si no, el rechazo."""
        from modules.marketplace.domain.models import Producto

        producto = Producto.objects.filter(id=producto_id).first()
        if producto is None or str(producto.edicion_id) != str(edicion_id):
            raise ProductoNoEncontradoError()
        return producto


__all__ = ["InventarioFlujo"]
