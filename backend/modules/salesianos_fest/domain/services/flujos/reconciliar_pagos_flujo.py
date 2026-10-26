"""
ReconciliarPagosFlujo — repairs paid orders whose commercial settlement is pending.

A verified payment marks its OrdenPago as PAGADA. The commercial settlement of
the linked Compra runs afterwards, in its own transaction, so a failure there
never rolls back the record of a real charge. When that settlement fails — or
when the data predates the automatic settlement — the order stays PAGADA while
its Compra stays PENDIENTE: the money is recorded but the purchase is not.

This flow closes that gap:
1. Selects the orders that are PAGADA and whose linked Compra is PENDIENTE.
2. Selects the SUCCESSFUL attempt of the order — the payment evidence — and
   tolerates the older pending attempts instead of mistaking them for it.
3. Verifies that the recorded payment matches the order (amount + currency).
4. Settles the purchase through `ConfirmarPagoFlujo`, the atomic owner of
   `Compra=PAGADA` + cup allocation, and expires the stale pending attempts.

Idempotent: running it again produces no change and never duplicates rights.

NOTE: it does NOT transition `Inscripcion.estado` — the administrative state
of an inscription is a separate concern from the commercial settlement.
"""
import logging

from asgiref.sync import sync_to_async
from injector import inject

from modules.pagos.domain.constants import OrdenPagoStatus
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.salesianos_fest.domain.constants import (
    EstadoReconciliacionPagoChoices,
    MotivoReconciliacionPagoChoices,
)
from modules.salesianos_fest.domain.results.reconciliacion_results import (
    ReconciliacionOrdenResult,
    ReconciliacionPagosResult,
)
from modules.salesianos_fest.domain.selectors import CompraSelector
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
    ConfirmarPagoFlujo,
)

logger = logging.getLogger(__name__)


class ReconciliarPagosFlujo:
    """
    Async flow that reconciles paid orders with a pending purchase.

    It is the business owner of the repair; the management command is only a
    thin entry point that parses the arguments and prints the report.
    """

    @inject
    def __init__(
        self,
        izipay_core: IzipayCoreService,
        compra_selector: CompraSelector,
        confirmar_pago_flujo: ConfirmarPagoFlujo,
    ):
        self.izipay_core = izipay_core
        self.compra_selector = compra_selector
        self.confirmar_pago_flujo = confirmar_pago_flujo

    async def _reconciliar(
        self,
        orden_pago_id: str | None = None,
        dry_run: bool = False,
    ) -> ReconciliacionPagosResult:
        """
        Reconcile the paid orders whose linked purchase is still pending.

        Args:
            orden_pago_id: Restrict the run to a single payment order (UUID).
            dry_run: Report what would be settled without changing anything.

        Returns:
            ReconciliacionPagosResult with the summary and the per-order detail.
        """
        candidatos = await sync_to_async(self._candidatos)(orden_pago_id)

        detalle: list[ReconciliacionOrdenResult] = []
        for orden, compra in candidatos:
            detalle.append(await self._reconciliar_orden(orden, compra, dry_run))

        return ReconciliacionPagosResult(
            dry_run=dry_run,
            revisadas=len(detalle),
            reconciliadas=self._contar(detalle, EstadoReconciliacionPagoChoices.RECONCILIADA),
            ya_liquidadas=self._contar(detalle, EstadoReconciliacionPagoChoices.YA_LIQUIDADA),
            omitidas=self._contar(detalle, EstadoReconciliacionPagoChoices.OMITIDA),
            errores=self._contar(detalle, EstadoReconciliacionPagoChoices.ERROR),
            detalle=detalle,
        )

    def _contar(self, detalle: list[ReconciliacionOrdenResult], estado: str) -> int:
        """Count the reviewed orders that ended in the given state."""
        return len([item for item in detalle if item.estado == estado])

    def _candidatos(self, orden_pago_id: str | None) -> list[tuple]:
        """Return the paid orders whose linked purchase is still pending."""
        candidatos = []
        for compra in self.compra_selector.listar_pendientes_con_orden_pago(orden_pago_id):
            orden = self.izipay_core.obtener_orden_pago_por_id(
                str(compra.orden_pago_id)
            )
            if orden is None or orden.estado != OrdenPagoStatus.PAGADA:
                continue
            candidatos.append((orden, compra))
        return candidatos

    async def _reconciliar_orden(self, orden, compra, dry_run: bool) -> ReconciliacionOrdenResult:
        """Reconcile a single paid order."""
        # 1. Payment evidence: only the successful attempt proves the charge.
        transaccion = await sync_to_async(
            self.izipay_core.obtener_intento_exitoso
        )(str(orden.id))
        if transaccion is None:
            return self._omitida(
                orden,
                compra,
                MotivoReconciliacionPagoChoices.SIN_PAGO_VERIFICADO,
            )

        # 2. The recorded payment must match the order — a purchase is never
        #    settled for an amount the order does not carry.
        if (
            transaccion.amount != orden.monto_total
            or transaccion.currency != orden.moneda
        ):
            logger.warning(
                "Reconciliation skipped for orden_pago %s: the recorded payment "
                "does not match the order",
                orden.id,
            )
            return self._omitida(
                orden,
                compra,
                MotivoReconciliacionPagoChoices.PAGO_NO_CORRELACIONADO,
                transaccion,
            )

        # 3. Dry run: report what would happen, change nothing.
        if dry_run:
            return self._omitida(
                orden,
                compra,
                MotivoReconciliacionPagoChoices.SIMULACION,
                transaccion,
            )

        # 4. Settle the purchase — atomic and idempotent.
        try:
            resultado = await self.confirmar_pago_flujo._confirmar_compra(str(orden.id))
        except Exception:
            logger.exception(
                "Reconciliation failed for orden_pago %s — the payment stays "
                "recorded and the purchase stays pending",
                orden.id,
            )
            return ReconciliacionOrdenResult(
                orden_pago_id=str(orden.id),
                numero_orden=orden.numero,
                estado=EstadoReconciliacionPagoChoices.ERROR,
                transaction_id=transaccion.transaction_id,
                compra_id=str(compra.id),
            )

        # 5. Close the stale pending attempts of the settled order: a settled
        #    order must not keep open attempts that look like charges.
        expirados = await sync_to_async(
            self.izipay_core.expirar_intentos_pendientes
        )(str(orden.id))

        estado = (
            EstadoReconciliacionPagoChoices.YA_LIQUIDADA
            if resultado.already_confirmed
            else EstadoReconciliacionPagoChoices.RECONCILIADA
        )

        return ReconciliacionOrdenResult(
            orden_pago_id=str(orden.id),
            numero_orden=orden.numero,
            estado=estado,
            transaction_id=transaccion.transaction_id,
            compra_id=str(compra.id),
            intentos_expirados=expirados,
        )

    def _omitida(
        self,
        orden,
        compra,
        motivo: str,
        transaccion=None,
    ) -> ReconciliacionOrdenResult:
        """Build the result of an order that was not settled in this run."""
        return ReconciliacionOrdenResult(
            orden_pago_id=str(orden.id),
            numero_orden=orden.numero,
            estado=EstadoReconciliacionPagoChoices.OMITIDA,
            motivo=motivo,
            transaction_id=transaccion.transaction_id if transaccion else None,
            compra_id=str(compra.id),
        )
