"""`PagoIntentoFlujo` — el ciclo de vida del intento de pago.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §1.3, §2.1 I-4, I-5)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Reglas congeladas que este flujo respeta:

- **Reabrir el checkout NO crea otra compra ni otra orden** (I-4). El flujo
  opera sobre la MISMA orden: retira el intento vivo anterior y crea uno
  nuevo, con su propia identidad y su propio ordinal.
- **Cerrar el modal NO cancela** (I-5). Este paquete no expone ninguna
  operación de cancelación: cerrar el checkout no emite ninguna orden de
  cancelación y la compra sigue `PENDIENTE` y recuperable.
- **Todo intento queda en la traza** (RN-C04). El intento retirado se marca
  `CANCELADO`, nunca se borra.

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`
(`contract/django-app-architecture-contract.md` §4.4).
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.pagos.domain.constants import EstadoOrdenPago
from modules.pagos.domain.exceptions import (
    OrdenPagoNoEncontradaError,
    OrdenPagoNoPagableError,
)
from modules.pagos.domain.results.pago_result import IntentoPagoResult
from modules.pagos.domain.services.core.orden_pago_core_service import (
    OrdenPagoCoreService,
)
from modules.pagos.domain.services.core.transaccion_pago_core_service import (
    TransaccionPagoCoreService,
)


class PagoIntentoFlujo:
    """Reabre el checkout de una orden creando un intento nuevo."""

    @inject
    def __init__(
        self,
        orden_core: OrdenPagoCoreService,
        transaccion_core: TransaccionPagoCoreService,
    ):
        self.orden_core = orden_core
        self.transaccion_core = transaccion_core

    async def abrir_intento(self, orden_pago_id) -> IntentoPagoResult:
        """Abre un intento de pago sobre la orden indicada.

        La orden NO se duplica: se reutiliza la existente. El intento vivo
        anterior se retira (queda en el historial) y el nuevo es el único vivo.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.

        Returns:
            El `IntentoPagoResult` del intento nuevo.

        Raises:
            OrdenPagoNoEncontradaError: si la orden no existe.
            OrdenPagoNoPagableError: si la orden ya no admite un pago.
        """
        try:
            return await sync_to_async(self._abrir_intento_sync)(orden_pago_id)
        except OrdenPagoNoEncontradaError:
            raise
        except OrdenPagoNoPagableError:
            raise

    @transaction.atomic()
    def _abrir_intento_sync(self, orden_pago_id) -> IntentoPagoResult:
        """Retira el intento vivo y crea el nuevo, con la orden bloqueada."""
        orden = self.orden_core.bloquear(orden_pago_id)
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        if orden.estado not in (
            EstadoOrdenPago.PENDIENTE,
            EstadoOrdenPago.EN_VERIFICACION,
            EstadoOrdenPago.FALLIDA,
        ):
            raise OrdenPagoNoPagableError()

        # 1. El intento vivo anterior se retira: se conserva como historial.
        self.transaccion_core.cerrar_intentos_vivos(orden.id)

        # 2. El intento nuevo tiene su propia identidad y su propio ordinal.
        ordinal = self.transaccion_core.contar_intentos(orden.id) + 1
        referencia = self.transaccion_core.generar_referencia_proveedor(
            orden.id, ordinal
        )
        intento = self.transaccion_core.crear_intento(
            orden_pago=orden,
            referencia_proveedor=referencia,
            metadata={},
        )

        return IntentoPagoResult(
            id=str(intento.id),
            intento=intento.intento,
            referencia_proveedor=intento.referencia_proveedor,
            estado=intento.estado,
            verificada=intento.verificada,
            codigo_respuesta=intento.codigo_respuesta,
            metodo_pago=intento.metodo_pago,
            creada_en=intento.created_at,
        )


__all__ = ["PagoIntentoFlujo"]
