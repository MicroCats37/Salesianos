"""
ConfirmarPagoFlujo — async flow for confirming a Compra after a verified payment.

Called after the payment was durably recorded (OrdenPago=PAGADA plus the
evidence that proves it: a correlated `TransaccionPago=EXITO` or an active
manual approval). This flow transitions commerce.Compra to PAGADA and
converts the paid capacity into rights (AsignacionCupo) for the preregistered
participants.

IMPORTANT: This does NOT transition Inscripcion to any state.
Inscripcion state transitions (CONFIRMADA, etc.) are handled in Phase 5+
with AsignacionCupo. A successful payment does NOT automatically confirm
the sports/administrative state of the Inscripcion.

ONE entry point:
`_confirmar_compra` — INTERNAL. Driven by the backend right after the
payment was durably recorded. There is no human actor to authorize: the
payment module itself is the only caller.

TRUTH PREDICATE: the purchase is only settled when the order proves it was
paid. An order with no correlated successful transaction and no active manual
approval is refused with `PAGO_NO_VERIFICADO` and grants nothing: a purchase
is never paid by assertion.

Flow:
1. Find commerce.Compra by orden_pago_id
2. Verify the payment evidence of the order (correlated Izipay transaction
   or active manual approval) — inside the settlement transaction
3. Mark Compra as PAGADA (within transaction.atomic for safety)
4. Allocate the paid capacity to the preregistered participants — deterministic
   order and idempotent: a repeated confirmation creates nothing new
5. Sync AcreditacionEvento for every person that received a right

TWO KINDS OF PURCHASE, ONE ENTRY POINT: the settlement is the same for both.
A SPORTS purchase allocates cupos; a PASS purchase (a batch of party passes)
is settled to PAGADA and allocates ZERO sports rights — its nominative rights
are materialized later, from the paid purchase.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.exceptions import PagoNoVerificadoError
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.salesianos_fest.domain.exceptions import CompraNotFoundError
from modules.salesianos_fest.domain.results.compra_results import CompraConfirmedResult
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService

logger = logging.getLogger(__name__)


class ConfirmarPagoFlujo:
    """
    Async flow for confirming a Compra after payment.

    Does NOT transition Inscripcion state.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
        evidencia_pago: EvidenciaPagoService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core
        self.evidencia_pago = evidencia_pago

    async def _confirmar_compra(
        self,
        orden_pago_id: str,
    ) -> CompraConfirmedResult:
        """
        Confirm a Compra after a verified payment (internal settlement).

        This entry point is driven by the backend right after the payment was
        durably recorded, so there is no human actor to authorize.

        Steps:
        1. Find commerce.Compra by orden_pago_id
        2. Verify the payment evidence of the order
        3. Mark Compra as PAGADA (within transaction.atomic)
        4. Allocate the paid capacity to the preregistered participants
        5. Return result

        Raises:
            CompraNotFoundError: the order has no linked purchase.
            PagoNoVerificadoError: the order carries no verifiable evidence.

        NOTE: Does NOT transition Inscripcion to any state.
              Inscripcion state is managed separately in Phase 5+.
        """
        return await sync_to_async(self._confirmar_sync)(orden_pago_id)

    @transaction.atomic()
    def _confirmar_sync(self, orden_pago_id: str) -> CompraConfirmedResult:
        """
        Sync version with transaction.atomic for safe concurrent confirmation.

        Idempotent: if Compra is already PAGADA, returns immediately with
        already_confirmed=True without raising an error. The allocation of the
        paid rights still runs (it is idempotent too), so a repeated payment
        confirmation never duplicates assignments.
        """
        compra = self._bloquear_compra(orden_pago_id)
        if compra is None:
            raise CompraNotFoundError()

        return self._liquidar_compra(compra)

    def _bloquear_compra(self, orden_pago_id: str) -> Compra | None:
        """
        Lock the purchase that funds the given payment order.

        `select_for_update` prevents two concurrent confirmations from
        allocating the same rights twice. The graph includes BOTH commercial
        compositions (`compra_inscripcion` and `compra_pase`) so the
        settlement knows what kind of purchase it is settling without an
        extra query per purchase. Returns None when the order has no linked
        purchase.

        `of=("self",)` locks ONLY the purchase row. The graph joins nullable
        relations (the order and the two compositions are optional), and
        PostgreSQL refuses `FOR UPDATE` on the nullable side of an outer
        join: without the explicit target the whole query fails on the
        production database. The purchase row is exactly what has to be
        serialized — the rights allocation takes its own locks.
        """
        return (
            Compra.objects
            .select_related(
                "orden_pago",
                "compra_inscripcion",
                "compra_inscripcion__inscripcion__evento",
                "compra_pase",
            )
            .select_for_update(of=("self",))
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )

    def _liquidar_compra(self, compra: Compra) -> CompraConfirmedResult:
        """
        Mark the purchase as paid and allocate its rights.

        The TRUTH PREDICATE runs first: the order must carry verifiable
        evidence of the payment (a correlated successful provider transaction
        or an active manual approval). Without it the purchase is never
        settled and no right is granted.

        Idempotent: if the Compra is already PAGADA it is reported as
        already confirmed instead of raising an error. The allocation of the
        paid rights is idempotent too, so a repeated payment confirmation
        never duplicates assignments.
        """
        self._verificar_evidencia(compra)

        # Idempotent: if already paid, do not raise — just report it
        already_confirmed = compra.estado != EstadoCompraChoices.PENDIENTE
        if not already_confirmed:
            # Mark as paid within the atomic transaction
            compra.estado = EstadoCompraChoices.PAGADA
            compra.save(update_fields=["estado", "updated_at"])

        # Phase 4: the paid capacity becomes rights for the preregistered
        # participants. Runs inside the confirmation transaction.
        if compra.estado == EstadoCompraChoices.PAGADA:
            self._asignar_derechos(compra)

        return CompraConfirmedResult(
            compra_id=str(compra.id),
            success=True,
            already_confirmed=already_confirmed,
        )

    def _verificar_evidencia(self, compra: Compra) -> None:
        """
        Refuse to settle a purchase whose order carries no payment evidence.

        The evidence is either a correlated successful provider transaction or
        an active manual approval. A purchase is never paid by assertion:
        without the proof nothing is settled and no right is granted.
        """
        orden_pago = getattr(compra, "orden_pago", None)
        if orden_pago is None:
            raise PagoNoVerificadoError()

        if not self.evidencia_pago.tiene_evidencia_pago(orden_pago):
            logger.warning(
                "Settlement refused: the order of the compra carries no "
                "verifiable payment evidence"
            )
            raise PagoNoVerificadoError()

    def _asignar_derechos(self, compra: Compra) -> None:
        """
        Convert the paid capacity of this compra into rights.

        A PASS purchase is a commercial batch, not a sports purchase: it
        grants ZERO sports rights — no cupo, no participant, no team and no
        accreditation. Its nominative rights are materialized later, from the
        paid purchase, by the beneficiary flow.

        A SPORTS purchase delegates the deterministic allocation to
        AsignacionCoreService and syncs AcreditacionEvento for every person
        that received a right.
        """
        if self._es_compra_de_pase(compra):
            logger.info(
                f"Compra {compra.id} is a pass purchase — no sports rights are assigned"
            )
            return

        compra_inscripcion = getattr(compra, "compra_inscripcion", None)
        if compra_inscripcion is None:
            logger.info(
                f"Compra {compra.id} has no inscripcion link — no rights to assign"
            )
            return

        inscripcion_id = str(compra_inscripcion.inscripcion_id)
        evento_id = str(compra_inscripcion.inscripcion.evento_id)

        asignaciones = self.asignacion_core.asignar_cupos_a_preregistrados(
            inscripcion_id=inscripcion_id,
            compra_preferida_id=str(compra.id),
        )

        for asignacion in asignaciones:
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=str(asignacion.inscripcion_persona.persona_id),
            )

        logger.info(
            f"Compra {compra.id} confirmed — {len(asignaciones)} rights assigned"
        )

    @staticmethod
    def _es_compra_de_pase(compra: Compra) -> bool:
        """True when the purchase is a batch of party passes."""
        return getattr(compra, "compra_pase", None) is not None
