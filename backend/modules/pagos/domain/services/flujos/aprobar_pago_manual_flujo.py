"""
AprobarPagoManualFlujo — async flow for the administrative approval of a
payment received outside the payment provider.

The flow answers ONE use case: an administrator proves that an order was
paid with money that arrived through a closed channel (bank transfer, cash,
Yape, Plin, other) and the purchase it funds must be settled.

Order of the operations (money first, settlement afterwards):

1. the capability must be enabled (`PAGO_MANUAL_APROBACION_ENABLED`),
2. the order is locked and loaded,
3. an ACTIVE approval already exists → the operation is idempotent and
   answers `YA_APROBADA` without writing anything,
4. the order already carries a successful provider transaction → refused
   (`ORDEN_YA_PAGADA_CON_IZIPAY`): a manual approval never contradicts the
   provider,
5. the purchase that funds the order is already cancelled → refused
   (`COMPRA_YA_CANCELADA`),
6. the approved amount and currency must match the order EXACTLY → refused
   (`MONTO_NO_COINCIDE`),
7. inside ONE transaction: the approval is written and the order becomes
   `PAGADA`,
8. AFTER that transaction commits, the commercial settlement is driven
   through the `IConfirmadorOrdenPagoService` port.

The evidence is durable BEFORE the settlement runs: a settlement failure
never erases the proof of a real payment, it only leaves the activation
pending, and the idempotent settlement converges on a later call.

It NEVER creates a `TransaccionPago`: a manual payment did not go through
the provider, and fabricating a provider transaction would corrupt the
reconciliation and the audit trail.
"""
import logging
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from injector import inject

from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    OrdenPagoStatus,
    SettlementStatus,
)
from modules.pagos.domain.exceptions import (
    AprobacionPagoManualDeshabilitadaError,
    CompraYaCanceladaError,
    MontoNoCoincideError,
    OrdenPagoNoEncontradaError,
    OrdenYaPagadaConIzipayError,
    PagoDatosInconsistentesError,
)
from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago
from modules.pagos.domain.ports import (
    IConfirmadorOrdenPagoService,
    IEstadoCompraOrdenPagoService,
)
from modules.pagos.domain.schemas.aprobacion_pago_manual_schemas import (
    AprobacionPagoManualData,
    AprobarPagoManualResult,
)
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)

logger = logging.getLogger(__name__)


class AprobarPagoManualFlujo:
    """Async flow of the administrative approval of a manual payment."""

    @inject
    def __init__(
        self,
        evidencia_pago: EvidenciaPagoService,
        confirmador_orden_pago: IConfirmadorOrdenPagoService,
        estado_compra_orden_pago: IEstadoCompraOrdenPagoService,
    ):
        self.evidencia_pago = evidencia_pago
        self.confirmador_orden_pago = confirmador_orden_pago
        self.estado_compra_orden_pago = estado_compra_orden_pago

    async def _aprobar_pago_manual(
        self,
        orden_pago_id: str,
        data: AprobacionPagoManualData,
        actor_id: str,
    ) -> AprobarPagoManualResult:
        """
        Register the manual approval of a payment order and settle its purchase.

        Args:
            orden_pago_id: UUID of the payment order to approve.
            data: the evidence (channel, reference, amount, currency, motive).
            actor_id: UUID of the administrator that approves.

        Returns:
            AprobarPagoManualResult.

        Raises:
            AprobacionPagoManualDeshabilitadaError: the capability is off.
            OrdenPagoNoEncontradaError: the order does not exist.
            OrdenYaPagadaConIzipayError: the order was already paid.
            CompraYaCanceladaError: the purchase was already cancelled.
            MontoNoCoincideError: the amount or the currency differ.
        """
        if not getattr(settings, "PAGO_MANUAL_APROBACION_ENABLED", False):
            raise AprobacionPagoManualDeshabilitadaError()

        registro = await sync_to_async(self._registrar_aprobacion)(
            orden_pago_id, data, actor_id
        )

        settlement_status = await self._liquidar_orden_pagada(orden_pago_id)

        return AprobarPagoManualResult(
            resultado=registro["resultado"],
            settlement_status=settlement_status,
            orden_pago_id=registro["orden_pago_id"],
            numero_orden=registro["numero_orden"],
            estado_orden=registro["estado_orden"],
            aprobacion_id=registro["aprobacion_id"],
            estado_aprobacion=registro["estado_aprobacion"],
            canal=registro["canal"],
            referencia=registro["referencia"],
            monto=registro["monto"],
            moneda=registro["moneda"],
            motivo=registro["motivo"],
            actor=registro["actor"],
            approved_at=registro["approved_at"],
        )

    # ── Persistencia ──────────────────────────────────────────────────────────

    @transaction.atomic()
    def _registrar_aprobacion(
        self,
        orden_pago_id: str,
        data: AprobacionPagoManualData,
        actor_id: str,
    ) -> dict:
        """
        Write the evidence of the manual payment (atomic).

        Idempotent: an order that already carries an ACTIVE approval answers
        `YA_APROBADA` and NOTHING is written — no second approval, no second
        settlement, no duplicated rights.
        """
        orden = (
            OrdenPago.objects
            .select_for_update()
            .filter(id=orden_pago_id)
            .first()
        )
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        # Idempotency: the evidence already exists.
        activa = (
            AprobacionPagoManual.objects
            .filter(
                orden_pago_id=orden.id,
                estado=EstadoAprobacionPagoManual.APROBADA,
            )
            .order_by("created_at")
            .first()
        )
        if activa is not None:
            return self._registro(orden, activa, resultado="YA_APROBADA")

        # A manual approval never contradicts the provider.
        if self.evidencia_pago.tiene_evidencia_izipay(orden):
            raise OrdenYaPagadaConIzipayError()

        # A cancelled purchase never becomes paid again.
        estado_compra = self.estado_compra_orden_pago.obtener_estado_compra(
            str(orden.id)
        )
        if estado_compra.cancelada:
            raise CompraYaCanceladaError()

        # The amount and the currency are exact: no implicit adjustment.
        if (
            Decimal(str(data.monto)) != Decimal(str(orden.monto_total))
            or data.moneda != orden.moneda
        ):
            raise MontoNoCoincideError()

        if orden.estado in (OrdenPagoStatus.CANCELADA, OrdenPagoStatus.VENCIDA):
            raise PagoDatosInconsistentesError()

        aprobacion = AprobacionPagoManual.objects.create(
            orden_pago=orden,
            actor_id=actor_id,
            canal=data.canal,
            referencia=data.referencia,
            monto=orden.monto_total,
            moneda=orden.moneda,
            motivo=data.motivo,
            estado=EstadoAprobacionPagoManual.APROBADA,
        )

        orden.estado = OrdenPagoStatus.PAGADA
        orden.pagada_en = timezone.now()
        orden.save(update_fields=["estado", "pagada_en", "updated_at"])

        logger.info(
            "Manual payment approval registered for orden_pago %s (canal=%s)",
            orden.id,
            data.canal,
        )

        return self._registro(orden, aprobacion, resultado="APROBADA")

    @staticmethod
    def _registro(
        orden: OrdenPago,
        aprobacion: AprobacionPagoManual,
        resultado: str,
    ) -> dict:
        """Build the durable projection of the approval."""
        return {
            "resultado": resultado,
            "orden_pago_id": str(orden.id),
            "numero_orden": orden.numero,
            "estado_orden": orden.estado,
            "aprobacion_id": str(aprobacion.id),
            "estado_aprobacion": aprobacion.estado,
            "canal": aprobacion.canal,
            "referencia": aprobacion.referencia,
            "monto": aprobacion.monto,
            "moneda": aprobacion.moneda,
            "motivo": aprobacion.motivo,
            "actor": getattr(aprobacion.actor, "username", "") or "",
            "approved_at": aprobacion.created_at,
        }

    # ── Liquidación ───────────────────────────────────────────────────────────

    async def _liquidar_orden_pagada(self, orden_pago_id: str) -> str:
        """
        Drive the commercial settlement of the paid order.

        The evidence is already committed when this runs: a settlement failure
        must never erase the proof of a real payment. Failures are logged and
        reported as `PENDING`; the settlement is idempotent, so a later call
        converges it.
        """
        try:
            resultado = await self.confirmador_orden_pago.confirmar_orden_pagada(
                orden_pago_id
            )
        except Exception:
            logger.exception(
                "Commercial settlement failed for the manually approved "
                "orden_pago %s — the evidence stays recorded and the activation "
                "stays pending",
                orden_pago_id,
            )
            return SettlementStatus.PENDING

        if not resultado.settled:
            logger.warning(
                "orden_pago %s has no purchase to settle — activation pending",
                orden_pago_id,
            )
            return SettlementStatus.PENDING

        return SettlementStatus.SETTLED


__all__ = ["AprobarPagoManualFlujo"]
