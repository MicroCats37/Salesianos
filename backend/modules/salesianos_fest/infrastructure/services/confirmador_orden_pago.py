"""
Adapter that settles the commercial side of a paid order.

`ConfirmadorOrdenPagoAdapter` implements `IConfirmadorOrdenPagoService`
(declared in `modules.pagos.domain.ports`) so that `pagos` can drive the
commercial settlement of a paid order without importing this module. The
dependency direction stays `salesianos_fest -> pagos`.
"""
import logging

from injector import inject

from modules.pagos.domain.ports import IConfirmadorOrdenPagoService
from modules.pagos.domain.schemas.result import SettlementResult
from modules.salesianos_fest.domain.exceptions import CompraNotFoundError
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
    ConfirmarPagoFlujo,
)

logger = logging.getLogger(__name__)


class ConfirmadorOrdenPagoAdapter(IConfirmadorOrdenPagoService):
    """
    Settles the commerce.Compra linked to a paid OrdenPago.

    Delegates to `ConfirmarPagoFlujo`, which is the atomic owner of
    `Compra=PAGADA` + cup allocation + accreditation. That flow is idempotent,
    so re-driving it after a partial failure converges instead of duplicating
    rights.

    NOTE: the adapter depends on the flow, not on `CompraOrchestrator`. The
    orchestrator pulls `IniciarPagoFlujo`, which pulls `PagosOrchestrator`,
    which pulls the port back — resolving it would create a DI cycle.
    """

    @inject
    def __init__(self, confirmar_pago_flujo: ConfirmarPagoFlujo):
        self.confirmar_pago_flujo = confirmar_pago_flujo

    async def confirmar_orden_pagada(self, orden_pago_id: str) -> SettlementResult:
        """
        Settle the purchase linked to a paid order.

        Args:
            orden_pago_id: UUID of the paid OrdenPago.

        Returns:
            SettlementResult(settled=True) when the purchase was settled (or
            was already paid), SettlementResult(settled=False) when no purchase
            is linked to the order — there is nothing to settle.

        Raises:
            CompraNotFoundError: never — a missing purchase is reported as
                "nothing to settle" instead of an error.
            Exception: any other failure is propagated so the caller can keep
                the recorded payment and report a pending activation.
        """
        try:
            result = await self.confirmar_pago_flujo._confirmar_compra(orden_pago_id)
        except CompraNotFoundError:
            logger.warning(
                "No compra linked to orden_pago %s — nothing to settle",
                orden_pago_id,
            )
            return SettlementResult(settled=False)

        return SettlementResult(
            settled=True,
            already_settled=result.already_confirmed,
        )


__all__ = ["ConfirmadorOrdenPagoAdapter"]
