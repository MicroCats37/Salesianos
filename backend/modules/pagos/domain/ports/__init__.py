"""
Domain ports for the pagos module.

A port is declared by the CONSUMER module and implemented by the PROVIDER
module. The implementation lives in the provider's `infrastructure/services.py`
and is bound in a registered DI module.

This keeps the module graph acyclic: `pagos` never imports `salesianos_fest`.
The port is expressed purely in payment vocabulary (`orden_pago_id`), so no
`commerce` or `salesianos_fest` type crosses the boundary.
"""
from abc import ABC, abstractmethod

from modules.pagos.domain.schemas.aprobacion_pago_manual_schemas import (
    EstadoCompraOrdenPago,
)
from modules.pagos.domain.schemas.result import SettlementResult


class IConfirmadorOrdenPagoService(ABC):
    """
    Port that settles the commercial side of a paid order.

    The consumer (`pagos`) drives it right after a payment is durably
    recorded, so the browser never has to confirm the purchase.
    """

    @abstractmethod
    async def confirmar_orden_pagada(self, orden_pago_id: str) -> SettlementResult:
        """
        Settle the purchase linked to a paid order.

        Idempotent: calling it again for an already settled order must not
        duplicate payments or rights.

        Args:
            orden_pago_id: UUID of the paid OrdenPago.

        Returns:
            SettlementResult describing the settlement outcome. A result with
            `settled=False` means there was nothing to settle — the caller
            decides whether that is a pending state or a no-op.

        Raises:
            Exception: any failure is surfaced to the caller. The caller owns
                the decision about the already recorded payment.
        """
        ...


class IPropietarioOrdenPagoService(ABC):
    """
    Port that resolves the owner of a payment order.

    The consumer (`pagos`) asks it before accepting a browser relay, so the
    payment module never imports the module that owns the commercial
    purchase. The port is expressed purely in payment vocabulary
    (`orden_pago_id` + `persona_id`).
    """

    @abstractmethod
    def es_propietario(self, orden_pago_id: str, persona_id: str) -> bool:
        """
        Return True when the person is the owner of the payment order.

        Args:
            orden_pago_id: UUID of the OrdenPago.
            persona_id: UUID of the authenticated person.

        Returns:
            True when the person may operate on that order.
        """
        ...


class IEstadoCompraOrdenPagoService(ABC):
    """
    Port that resolves the commercial state of the purchase funding an order.

    The consumer (`pagos`) needs it to refuse the manual approval of a
    purchase that was already cancelled. The purchase aggregate belongs to
    `commerce`, so the payment module asks for this tiny projection instead
    of importing it: the dependency direction stays `commerce -> pagos`.
    """

    @abstractmethod
    def obtener_estado_compra(self, orden_pago_id: str) -> EstadoCompraOrdenPago:
        """
        Return the commercial state of the purchase that funds an order.

        Args:
            orden_pago_id: UUID of the OrdenPago.

        Returns:
            EstadoCompraOrdenPago with `existe=False` when no purchase funds
            the order, or with the commercial state of that purchase.
        """
        ...


__all__ = [
    "IConfirmadorOrdenPagoService",
    "IEstadoCompraOrdenPagoService",
    "IPropietarioOrdenPagoService",
]
