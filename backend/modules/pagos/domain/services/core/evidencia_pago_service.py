"""
EvidenciaPagoService — the TRUTH predicate of a payment.

A payment order is paid ONLY when it carries verifiable evidence:

- a provider transaction with status `EXITO` **correlated** with the order
  (same order, same amount, same currency), or
- an active (`APROBADA`) manual approval with matching amount and currency.

Everything else is `SIN_PAGO`. The predicate is the single gate that the
commercial settlement consults before it turns a purchase into `PAGADA` and
allocates rights: without evidence there is nothing to settle.

The service is a SYNC core service: it opens no transaction of its own and it
never writes.
"""
from decimal import Decimal

from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrigenPago,
)
from modules.pagos.domain.models import AprobacionPagoManual, TransaccionPago


def _mismo_monto(monto_a, monto_b) -> bool:
    """Compare two monetary amounts without floating point noise."""
    return Decimal(str(monto_a)) == Decimal(str(monto_b))


class EvidenciaPagoService:
    """Read-only predicate of the payment evidence of an order."""

    @staticmethod
    def origenes_por_ordenes(ordenes: dict[str, object]) -> dict[str, str]:
        """Return evidence origins for a page of orders without N+1 queries."""
        if not ordenes:
            return {}

        orden_ids = list(ordenes)
        manuales = {
            str(orden_pago_id)
            for orden_pago_id, monto, moneda in AprobacionPagoManual.objects.filter(
                orden_pago_id__in=orden_ids,
                estado=EstadoAprobacionPagoManual.APROBADA,
            ).values_list("orden_pago_id", "monto", "moneda")
            if _mismo_monto(monto, ordenes[str(orden_pago_id)].monto_total)
            and moneda == ordenes[str(orden_pago_id)].moneda
        }
        izipay = {
            str(orden_pago_id)
            for orden_pago_id, monto, moneda in TransaccionPago.objects.filter(
                orden_pago_id__in=orden_ids,
                status=IzipayStatus.EXITO,
            ).values_list("orden_pago_id", "amount", "currency")
            if _mismo_monto(monto, ordenes[str(orden_pago_id)].monto_total)
            and moneda == ordenes[str(orden_pago_id)].moneda
        }

        return {
            orden_id: (
                OrigenPago.MANUAL if orden_id in manuales
                else OrigenPago.IZIPAY if orden_id in izipay
                else OrigenPago.SIN_PAGO
            )
            for orden_id in orden_ids
        }

    def tiene_evidencia_izipay(self, orden_pago) -> bool:
        """
        Return True when the order carries a CORRELATED successful transaction.

        The correlation is what makes the evidence trustworthy: the attempt
        must belong to the order AND match its amount and currency. A
        transaction of another order, or of another amount, is not evidence
        for this one.
        """
        if orden_pago is None:
            return False

        return TransaccionPago.objects.filter(
            orden_pago_id=orden_pago.id,
            status=IzipayStatus.EXITO,
            amount=orden_pago.monto_total,
            currency=orden_pago.moneda,
        ).exists()

    def tiene_aprobacion_manual_activa(self, orden_pago) -> bool:
        """
        Return True when the order carries an ACTIVE manual approval.

        The approval must match the amount and the currency of the order: an
        approval of a different amount is not evidence of THIS payment.
        """
        if orden_pago is None:
            return False

        return AprobacionPagoManual.objects.filter(
            orden_pago_id=orden_pago.id,
            estado=EstadoAprobacionPagoManual.APROBADA,
            monto=orden_pago.monto_total,
            moneda=orden_pago.moneda,
        ).exists()

    def tiene_evidencia_pago(self, orden_pago) -> bool:
        """Return True when the order carries ANY verifiable payment evidence."""
        return (
            self.tiene_evidencia_izipay(orden_pago)
            or self.tiene_aprobacion_manual_activa(orden_pago)
        )

    def origen_pago(self, orden_pago) -> str:
        """
        Return the origin of the payment evidence of the order.

        `IZIPAY`, `MANUAL` or `SIN_PAGO`. The origin is DERIVED from the
        evidence: it is never a field an administrator can type.
        """
        if self.tiene_aprobacion_manual_activa(orden_pago):
            return OrigenPago.MANUAL
        if self.tiene_evidencia_izipay(orden_pago):
            return OrigenPago.IZIPAY
        return OrigenPago.SIN_PAGO


__all__ = ["EvidenciaPagoService"]
