"""
ConfirmarPagoFlujo — async flow for confirming a Compra after Izipay payment.

Called after PagosOrchestrator confirms the payment (OrdenPago=PAGADA, TransaccionPago=EXITO).
This flow transitions commerce.Compra to PAGADA and converts the paid capacity
into rights (AsignacionCupo) for the preregistered participants.

IMPORTANT: This does NOT transition Inscripcion to any state.
Inscripcion state transitions (CONFIRMADA, etc.) are handled in Phase 5+
with AsignacionCupo. A successful payment does NOT automatically confirm
the sports/administrative state of the Inscripcion.

Two entry points:
1. `_confirmar_compra` — INTERNAL. Driven by the backend right after the
   payment was durably recorded. There is no human actor to authorize, so it
   settles the purchase directly.
2. `_confirmar_compra_autorizada` — MANUAL RECOVERY, driven by an
   authenticated caller. The caller must be the responsible of the
   inscription linked to the purchase, or a Django administrator. The
   authorization is evaluated inside the settlement transaction and BEFORE
   any write, so a refused request leaves the purchase, the payment order
   and the cup rights untouched.

Flow:
1. Find commerce.Compra by orden_pago_id
2. Validate Compra is PENDIENTE
3. Mark Compra as PAGADA (within transaction.atomic for safety)
4. Allocate the paid capacity to the preregistered participants — deterministic
   order and idempotent: a repeated confirmation creates nothing new
5. Sync AcreditacionEvento for every person that received a right
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.exceptions import (
    CompraNoAutorizadoError,
    CompraNotFoundError,
)
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
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    async def _confirmar_compra(
        self,
        orden_pago_id: str,
    ) -> CompraConfirmedResult:
        """
        Confirm a Compra after successful payment (internal settlement).

        This entry point is driven by the backend right after the payment was
        durably recorded, so there is no human actor to authorize. The manual
        recovery path uses `_confirmar_compra_autorizada`.

        Steps:
        1. Find commerce.Compra by orden_pago_id
        2. Validate Compra is PENDIENTE
        3. Mark Compra as PAGADA (within transaction.atomic)
        4. Allocate the paid capacity to the preregistered participants
        5. Return result

        NOTE: Does NOT transition Inscripcion to any state.
              Inscripcion state is managed separately in Phase 5+.
        """
        return await sync_to_async(self._confirmar_sync)(orden_pago_id)

    async def _confirmar_compra_autorizada(
        self,
        orden_pago_id: str,
        persona_id: str | None,
        es_admin: bool,
    ) -> CompraConfirmedResult:
        """
        Confirm a Compra on behalf of an authenticated caller (manual recovery).

        The caller must be the responsible of the inscription linked to the
        purchase, or a Django administrator. The authorization is evaluated
        inside the settlement transaction and before any write, so a refused
        request leaves the Compra, the OrdenPago and the cup rights untouched.

        Args:
            orden_pago_id: UUID of the payment order that funds the purchase.
            persona_id: UUID of the authenticated person (None for admins).
            es_admin: True when the caller has administrative authority.

        Raises:
            CompraNotFoundError: the order has no linked purchase.
            CompraNoAutorizadoError: the caller does not own the purchase.
        """
        return await sync_to_async(self._confirmar_autorizada_sync)(
            orden_pago_id, persona_id, es_admin
        )

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

    @transaction.atomic()
    def _confirmar_autorizada_sync(
        self,
        orden_pago_id: str,
        persona_id: str | None,
        es_admin: bool,
    ) -> CompraConfirmedResult:
        """
        Authorized variant of `_confirmar_sync`.

        The ownership check runs inside the same transaction as the settlement
        and BEFORE any write: a refused caller changes nothing.

        Raises:
            CompraNotFoundError: the order has no linked purchase.
            CompraNoAutorizadoError: the caller does not own the purchase.
        """
        compra = self._bloquear_compra(orden_pago_id)
        if compra is None:
            raise CompraNotFoundError()

        if not es_admin and not self._es_responsable(compra, persona_id):
            logger.warning(
                "Manual commercial recovery refused: the caller is not the "
                "responsible of the inscription linked to the purchase"
            )
            raise CompraNoAutorizadoError()

        return self._liquidar_compra(compra)

    def _bloquear_compra(self, orden_pago_id: str) -> Compra | None:
        """
        Lock the purchase that funds the given payment order.

        `select_for_update` prevents two concurrent confirmations from
        allocating the same rights twice. Returns None when the order has no
        linked purchase.
        """
        return (
            Compra.objects
            .select_related(
                "orden_pago",
                "compra_inscripcion",
                "compra_inscripcion__inscripcion__evento",
            )
            .select_for_update()
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )

    def _es_responsable(self, compra: Compra, persona_id: str | None) -> bool:
        """
        Return True when the person is the responsible of the linked inscription.

        The owner of a purchase is the responsible of the inscription it
        funds. A purchase without an inscription link has no owner: nobody can
        recover it manually (only the backend settlement can settle it).
        """
        if not persona_id:
            return False

        compra_inscripcion = getattr(compra, "compra_inscripcion", None)
        if compra_inscripcion is None:
            return False

        inscripcion = getattr(compra_inscripcion, "inscripcion", None)
        if inscripcion is None:
            return False

        return str(inscripcion.responsable_id) == str(persona_id)

    def _liquidar_compra(self, compra: Compra) -> CompraConfirmedResult:
        """
        Mark the purchase as paid and allocate its rights.

        Idempotent: if the Compra is already PAGADA it is reported as
        already confirmed instead of raising an error. The allocation of the
        paid rights is idempotent too, so a repeated payment confirmation
        never duplicates assignments.
        """
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

    def _asignar_derechos(self, compra: Compra) -> None:
        """
        Convert the paid capacity of this compra into rights.

        Delegates the deterministic allocation to AsignacionCoreService and
        syncs AcreditacionEvento for every person that received a right.
        """
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
