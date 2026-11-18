"""
EstadoOperativoPagoService — the SINGLE owner of the payment operator verdict.

The administrative payments table used to publish three sibling facts — the
commercial state of the purchase, the state of the order and the origin of the
evidence — and let the reader compare them. This service publishes ONE verdict
instead: the answer to "is this payment done?".

The verdict is DERIVED, never typed: it is a pure function of the facts that
already exist.

The rules are evaluated IN THIS ORDER (the first match wins):

1. `SIN_ORDEN`            — the purchase has no payment order.
2. `PAGADA_SIN_LIQUIDAR`  — the order is paid but the purchase is not.
3. `PAGADA_SIN_EVIDENCIA` — the order is paid but carries no correlated
                            evidence (no successful provider transaction and no
                            active manual approval).
4. `PAGADA_SIN_FECHA`     — the order is paid and evidenced, but it has no
                            payment date.
5. `PAGADA`               — the order is paid, the purchase is paid, the
                            evidence is present and the payment is dated.
6. `VENCIDA`              — the order expired.
7. `CANCELADA`            — the order or the purchase was cancelled.
8. `PENDIENTE`            — the payment has not happened yet.

A paid order NEVER yields `CANCELADA` nor `VENCIDA`: the order state wins
first, so the reader is never told that a paid payment was cancelled.

The service owns the PRECEDENCE, never the data: it receives the facts of one
order and returns its verdict. It never queries the database and never writes.

The evidence is the one published by `EvidenciaPagoService`: `IZIPAY` (a
CORRELATED successful transaction) or `MANUAL` (an ACTIVE approval with a
matching amount and currency). `SIN_PAGO` means there is nothing to verify.
"""
from datetime import datetime

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import (
    EstadoOperativoPago,
    OrigenPago,
    OrdenPagoStatus,
)


class EstadoOperativoPagoService:
    """The operator verdict of a payment order."""

    @staticmethod
    def calcular(
        *,
        estado_orden: str | None,
        estado_compra: str,
        origen_pago: str,
        pagada_en: datetime | None,
    ) -> str:
        """
        Return the operator verdict of one payment.

        Args:
            estado_orden: the state of the payment order (`None` when the
                purchase has no order).
            estado_compra: the commercial state of the purchase.
            origen_pago: the origin of the evidence of the order
                (`IZIPAY`, `MANUAL` or `SIN_PAGO`).
            pagada_en: the payment date of the order (`None` when the order
                was never dated).

        Returns:
            One code of `EstadoOperativoPago`.
        """
        if not estado_orden:
            return EstadoOperativoPago.SIN_ORDEN

        if estado_orden == OrdenPagoStatus.PAGADA:
            if estado_compra != EstadoCompraChoices.PAGADA:
                return EstadoOperativoPago.PAGADA_SIN_LIQUIDAR

            if origen_pago == OrigenPago.SIN_PAGO:
                return EstadoOperativoPago.PAGADA_SIN_EVIDENCIA

            if pagada_en is None:
                return EstadoOperativoPago.PAGADA_SIN_FECHA

            return EstadoOperativoPago.PAGADA

        if estado_orden == OrdenPagoStatus.VENCIDA:
            return EstadoOperativoPago.VENCIDA

        if (
            estado_orden == OrdenPagoStatus.CANCELADA
            or estado_compra == EstadoCompraChoices.CANCELADA
        ):
            return EstadoOperativoPago.CANCELADA

        return EstadoOperativoPago.PENDIENTE


__all__ = ["EstadoOperativoPagoService"]
