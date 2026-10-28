"""
CancelarCompraFlujo — async flow for cancelling a Compra (refund / abandoned payment).

Called when:
- The payment of a Compra is refunded
- A pending Compra is abandoned by the buyer
- An administrator annuls the MANUAL approval of a payment (audited)
- An administrator cancels a PASS purchase (audited, not a monetary refund)

Flow:
1. Lock the commerce.Compra (SELECT FOR UPDATE) — safe against concurrent refunds
2. Mark the Compra as CANCELADA (idempotent: an already cancelled Compra is a no-op)
3. Revoke ONLY the ACTIVA AsignacionCupo derived from that Compra — assignments
   funded by other compras keep their right
4. Revoke the ACTIVA PaseBeneficiario of that Compra — the nominative rights
   it funded are consumed forever
5. Retire the Participacion that was backed by a revoked right (a revoked right
   cannot back an active participation)
6. Recalculate AcreditacionEvento for every affected persona, considering ALL
   their inscriptions (R10 — the person may still have access elsewhere)

MANUAL APPROVAL:
- a purchase funded by an ACTIVE manual approval can NEVER be cancelled by
  its owner: only the administrative annulment revokes it, because that
  annulment is the audited decision,
- `_anular_pago_manual` is that administrative annulment: it marks the
  approval `ANULADA` (actor, date and motive), the order `CANCELADA` and the
  purchase `CANCELADA`, and then revokes the rights with the SAME canonical
  revocation. It is idempotent: repeating it answers `YA_ANULADA`.

PASS PURCHASES:
- the ordinary cancellation of a purchase is an operation of the BUYER: it
  can never cancel a pass purchase, because that revokes nominative rights
  already delivered. It is refused with a typed error,
- `_cancelar_compra_pase` is the administrative cancellation: it cancels the
  purchase AND its order, revokes the pass rights with the SAME canonical
  revocation and recomputes the effective access. It is NOT a monetary
  refund.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from injector import inject

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    OrdenPagoStatus,
)
from modules.pagos.domain.exceptions import (
    AprobacionPagoManualNoEncontradaError,
)
from modules.pagos.domain.models import AprobacionPagoManual
from modules.salesianos_fest.domain.exceptions import (
    CompraConAprobacionManualError,
    CompraNotFoundError,
    PaseCancelacionRequiereAdministracionError,
    PaseCompraNoEncontradaError,
)
from modules.salesianos_fest.domain.results.anulacion_pago_manual_results import (
    AnularPagoManualResult,
)
from modules.salesianos_fest.domain.results.compra_results import CompraCanceladaResult
from modules.salesianos_fest.domain.results.pase_results import PaseCompraCanceladaResult
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
from modules.salesianos_fest.domain.services.core.pase_beneficiario_service import (
    PaseBeneficiarioCoreService,
)

logger = logging.getLogger(__name__)

MOTIVO_REVOCACION = "Cancelación de la compra"


class CancelarCompraFlujo:
    """
    Async flow for cancelling a Compra and revoking the rights it funded.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
        pase_beneficiario_core: PaseBeneficiarioCoreService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core
        self.pase_beneficiario_core = pase_beneficiario_core

    async def _cancelar_compra(self, compra_id: str) -> CompraCanceladaResult:
        """Cancel a Compra and revoke the rights derived from it."""
        return await sync_to_async(self._cancelar_sync)(compra_id)

    async def _cancelar_compra_pase(
        self,
        compra_id: str,
        actor_id: str,
        motivo: str,
    ) -> PaseCompraCanceladaResult:
        """
        Cancel a PASS purchase (administrative).

        The purchase and its order are cancelled, the nominative rights it
        funded are revoked with the SAME canonical revocation and the
        effective access of every affected person is recomputed.

        It is NOT a monetary refund: no money is returned by this operation.

        Args:
            compra_id: UUID of the commerce.Compra.
            actor_id: UUID of the administrator that cancels it.
            motivo: Why the purchase is cancelled (audited, mandatory).

        Raises:
            PaseCompraNoEncontradaError: the purchase is not a pass purchase.
        """
        return await sync_to_async(self._cancelar_compra_pase_sync)(
            compra_id, actor_id, motivo
        )

    async def _anular_pago_manual(
        self,
        orden_pago_id: str,
        actor_id: str,
        motivo: str,
    ) -> AnularPagoManualResult:
        """
        Annul the manual approval of a payment order (administrative).

        The approval, the order and the purchase are updated INSIDE ONE
        transaction and the rights are revoked with the canonical revocation.

        Args:
            orden_pago_id: UUID of the payment order.
            actor_id: UUID of the administrator that annuls the approval.
            motivo: Why the approval is annulled (audited).

        Raises:
            AprobacionPagoManualNoEncontradaError: the order has no approval.
            CompraNotFoundError: the order has no linked purchase.
        """
        return await sync_to_async(self._anular_sync)(
            orden_pago_id, actor_id, motivo
        )

    @transaction.atomic()
    def _cancelar_sync(self, compra_id: str) -> CompraCanceladaResult:
        """
        Sync version with transaction.atomic for safe concurrent cancellation.

        Idempotent: cancelling an already cancelled Compra returns the same
        summary without revoking anything twice.
        """
        from modules.salesianos_fest.domain.models import AsignacionCupo, Participacion
        from modules.salesianos_fest.domain.constants import (
            EstadoAsignacionCupoChoices,
            EstadoParticipacionChoices,
        )

        compra = (
            Compra.objects
            .select_related(
                "orden_pago",
                "compra_inscripcion",
                "compra_inscripcion__inscripcion__evento",
            )
            .select_for_update(of=("self",))
            .filter(id=compra_id)
            .first()
        )
        if compra is None:
            raise CompraNotFoundError()

        # A PASS purchase is cancelled by an ADMINISTRATOR: revoking the
        # nominative rights it already delivered is an audited decision, not
        # an operation of the buyer.
        if self._es_compra_de_pase(compra):
            raise PaseCancelacionRequiereAdministracionError()

        compra_inscripcion = getattr(compra, "compra_inscripcion", None)
        inscripcion_id = (
            str(compra_inscripcion.inscripcion_id) if compra_inscripcion else ""
        )

        # A purchase funded by an ACTIVE manual approval is only revoked by the
        # administrative annulment: that decision is audited and this one is
        # not.
        if self._tiene_aprobacion_manual_activa(compra):
            raise CompraConAprobacionManualError()

        # Idempotent: an already cancelled Compra does not revoke anything again
        if compra.estado == EstadoCompraChoices.CANCELADA:
            return CompraCanceladaResult(
                compra_id=str(compra.id),
                inscripcion_id=inscripcion_id,
                estado=compra.estado,
                ya_cancelada=True,
                asignaciones_revocadas=0,
                personas_afectadas=0,
            )

        # Only the rights funded by THIS compra are affected
        asignaciones = list(
            AsignacionCupo.objects
            .filter(
                compra_id=compra.id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            .select_related(
                "inscripcion",
                "inscripcion__evento",
                "inscripcion_persona",
                "inscripcion_persona__persona",
            )
        )

        # Cancel the compra
        compra.estado = EstadoCompraChoices.CANCELADA
        compra.save(update_fields=["estado", "updated_at"])

        personas_afectadas, _asignaciones, _beneficiarios = self._revocar_derechos(
            compra, asignaciones, None, MOTIVO_REVOCACION
        )

        logger.info(
            f"Compra {compra.id} cancelled — {len(asignaciones)} rights revoked, "
            f"{len(personas_afectadas)} personas recalculated"
        )

        return CompraCanceladaResult(
            compra_id=str(compra.id),
            inscripcion_id=inscripcion_id,
            estado=compra.estado,
            ya_cancelada=False,
            asignaciones_revocadas=len(asignaciones),
            personas_afectadas=len(personas_afectadas),
        )

    @transaction.atomic()
    def _cancelar_compra_pase_sync(
        self,
        compra_id: str,
        actor_id: str,
        motivo: str,
    ) -> PaseCompraCanceladaResult:
        """
        Sync version with transaction.atomic of the administrative
        cancellation of a pass purchase.
        """
        from modules.salesianos_fest.domain.models import CompraPase, PaseBeneficiario
        from modules.salesianos_fest.domain.constants import (
            EstadoPaseBeneficiarioChoices,
        )

        # 1. The purchase (locked).
        compra = (
            Compra.objects
            .select_related("orden_pago")
            .select_for_update(of=("self",))
            .filter(id=compra_id)
            .first()
        )
        if compra is None:
            raise CompraNotFoundError()

        # 2. It must be a PASS purchase: a sports purchase is not cancelled
        #    here (it keeps its own canonical path).
        linea = CompraPase.objects.filter(compra_id=compra.id).first()
        if linea is None:
            raise PaseCompraNoEncontradaError()

        orden_pago = compra.orden_pago

        # 3. Idempotent: an already cancelled purchase revokes nothing again.
        if compra.estado == EstadoCompraChoices.CANCELADA:
            return PaseCompraCanceladaResult(
                compra_id=str(compra.id),
                estado_compra=compra.estado,
                estado_orden=orden_pago.estado if orden_pago else "",
                ya_cancelada=True,
                beneficiarios_revocados=0,
                personas_afectadas=0,
                motivo=motivo,
            )

        # 4. The purchase and its order are cancelled.
        compra.estado = EstadoCompraChoices.CANCELADA
        compra.save(update_fields=["estado", "updated_at"])

        if orden_pago is not None:
            orden_pago.estado = OrdenPagoStatus.CANCELADA
            orden_pago.save(update_fields=["estado", "updated_at"])

            # The evidence of a MANUAL payment must not stay ACTIVE on a
            # cancelled order: the approval is annulled in the SAME canonical
            # operation (actor, date and motive). The provider transaction of
            # an Izipay payment is IMMUTABLE and is never touched.
            self._anular_aprobacion_manual(orden_pago, actor_id, motivo)

        # 5. The canonical revocation of the pass rights.
        beneficiarios_activos = PaseBeneficiario.objects.filter(
            compra_pase__compra_id=compra.id,
            estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        ).count()
        personas_afectadas, _asignaciones, _beneficiarios = self._revocar_derechos(
            compra, [], actor_id, motivo
        )

        logger.info(
            "Pass purchase %s cancelled by the administration — %s rights "
            "revoked, %s personas recalculated",
            compra.id,
            beneficiarios_activos,
            len(personas_afectadas),
        )

        return PaseCompraCanceladaResult(
            compra_id=str(compra.id),
            estado_compra=compra.estado,
            estado_orden=orden_pago.estado if orden_pago else "",
            ya_cancelada=False,
            beneficiarios_revocados=beneficiarios_activos,
            personas_afectadas=len(personas_afectadas),
            motivo=motivo,
        )

    @transaction.atomic()
    def _anular_sync(
        self,
        orden_pago_id: str,
        actor_id: str,
        motivo: str,
    ) -> AnularPagoManualResult:
        """
        Sync version with transaction.atomic of the administrative annulment.
        """
        from modules.salesianos_fest.domain.models import AsignacionCupo
        from modules.salesianos_fest.domain.constants import (
            EstadoAsignacionCupoChoices,
        )

        # 1. The approval of the order (locked).
        aprobacion = (
            AprobacionPagoManual.objects
            .select_for_update()
            .filter(orden_pago_id=orden_pago_id)
            .order_by("-created_at")
            .first()
        )
        if aprobacion is None:
            raise AprobacionPagoManualNoEncontradaError()

        compra = (
            Compra.objects
            .select_related(
                "orden_pago",
                "compra_inscripcion",
                "compra_inscripcion__inscripcion__evento",
            )
            .select_for_update(of=("self",))
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )
        if compra is None:
            raise CompraNotFoundError()

        orden_pago = compra.orden_pago

        # 2. Idempotency: an already annulled approval revokes nothing again.
        if aprobacion.estado == EstadoAprobacionPagoManual.ANULADA:
            return AnularPagoManualResult(
                resultado="YA_ANULADA",
                orden_pago_id=str(orden_pago.id),
                compra_id=str(compra.id),
                estado_compra=compra.estado,
                estado_orden=orden_pago.estado,
                estado_aprobacion=aprobacion.estado,
                asignaciones_revocadas=0,
                beneficiarios_revocados=0,
                personas_afectadas=0,
                anulada_por=getattr(aprobacion.anulada_por, "username", "") or "",
                anulada_en=aprobacion.anulada_en,
                motivo_anulacion=aprobacion.motivo_anulacion or "",
            )

        asignaciones = list(
            AsignacionCupo.objects
            .filter(
                compra_id=compra.id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            .select_related(
                "inscripcion",
                "inscripcion__evento",
                "inscripcion_persona",
                "inscripcion_persona__persona",
            )
        )

        # 3. The audited transition of the approval.
        aprobacion.estado = EstadoAprobacionPagoManual.ANULADA
        aprobacion.anulada_por_id = actor_id
        aprobacion.anulada_en = timezone.now()
        aprobacion.motivo_anulacion = motivo
        aprobacion.save(
            update_fields=[
                "estado",
                "anulada_por",
                "anulada_en",
                "motivo_anulacion",
                "updated_at",
            ]
        )

        # 4. The order and the purchase are cancelled too.
        orden_pago.estado = OrdenPagoStatus.CANCELADA
        orden_pago.save(update_fields=["estado", "updated_at"])

        compra.estado = EstadoCompraChoices.CANCELADA
        compra.save(update_fields=["estado", "updated_at"])

        # 5. The canonical revocation of the rights — the pass rights of a
        #    pass purchase are revoked here too.
        personas_afectadas, asignaciones_revocadas, beneficiarios_revocados = (
            self._revocar_derechos(compra, asignaciones, actor_id, motivo)
        )

        logger.info(
            "Manual payment approval annulled for orden_pago %s — %s rights "
            "revoked, %s personas recalculated",
            orden_pago.id,
            len(asignaciones),
            len(personas_afectadas),
        )

        return AnularPagoManualResult(
            resultado="ANULADA",
            orden_pago_id=str(orden_pago.id),
            compra_id=str(compra.id),
            estado_compra=compra.estado,
            estado_orden=orden_pago.estado,
            estado_aprobacion=aprobacion.estado,
            asignaciones_revocadas=asignaciones_revocadas,
            beneficiarios_revocados=beneficiarios_revocados,
            personas_afectadas=len(personas_afectadas),
            anulada_por=getattr(aprobacion.anulada_por, "username", "") or "",
            anulada_en=aprobacion.anulada_en,
            motivo_anulacion=motivo,
        )

    # ── Internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _es_compra_de_pase(compra: Compra) -> bool:
        """True when the purchase is a batch of party passes."""
        from modules.salesianos_fest.domain.models import CompraPase

        return CompraPase.objects.filter(compra_id=compra.id).exists()

    @staticmethod
    def _tiene_aprobacion_manual_activa(compra: Compra) -> bool:
        """Return True when the purchase carries an ACTIVE manual approval."""
        if not compra.orden_pago_id:
            return False

        return AprobacionPagoManual.objects.filter(
            orden_pago_id=compra.orden_pago_id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).exists()

    def _revocar_derechos(
        self,
        compra: Compra,
        asignaciones,
        actor_id: str | None = None,
        motivo: str = MOTIVO_REVOCACION,
    ) -> tuple[dict[str, str], int, int]:
        """
        Revoke the rights of a purchase and recalculate the affected access.

        This is the CANONICAL revocation: it is used by the ordinary
        cancellation AND by the administrative annulment AND by the
        administrative cancellation of a pass purchase, so all the paths retire
        the same participations, revoke the same pass rights and recalculate
        the same accreditations.

        Revoking a pass removes ONLY that source: a sports benefit or an
        AUTORIZADA override may keep the fiesta access.

        Returns:
            `(personas_afectadas, asignaciones_revocadas,
            beneficiarios_revocados)`: the affected people (persona_id ->
            evento_id) and the two counts, reported SEPARATELY because a sports
            assignment and a pass right are different rights.
        """
        from modules.salesianos_fest.domain.models import Participacion
        from modules.salesianos_fest.domain.constants import (
            EstadoParticipacionChoices,
        )

        personas_afectadas: dict[str, str] = {}  # persona_id -> evento_id
        for asignacion in asignaciones:
            self.asignacion_core.revocar_asignacion(
                asignacion,
                motivo=MOTIVO_REVOCACION,
            )
            personas_afectadas[str(asignacion.inscripcion_persona.persona_id)] = str(
                asignacion.inscripcion.evento_id
            )

            # A revoked right cannot back an active participation
            Participacion.objects.filter(
                inscripcion_persona_id=asignacion.inscripcion_persona_id,
                estado=EstadoParticipacionChoices.ACTIVA,
            ).update(estado=EstadoParticipacionChoices.RETIRADA)

        # The nominative rights of a pass purchase, revoked with the SAME
        # canonical branch.
        pass_afectados = self.pase_beneficiario_core.revocar_activos(
            compra,
            actor_id,
            motivo,
        )
        for persona_id, evento_id in pass_afectados:
            personas_afectadas[persona_id] = evento_id

        # Recalculate the rights of every affected persona (all inscriptions)
        for persona_id, evento_id in personas_afectadas.items():
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=persona_id,
            )

        return personas_afectadas, len(asignaciones), len(pass_afectados)

    @staticmethod
    def _anular_aprobacion_manual(
        orden_pago,
        actor_id: str,
        motivo: str,
    ) -> None:
        """
        Annul the ACTIVE manual approval of an order, if it has one.

        A cancelled order must not keep ACTIVE evidence of a payment: the
        approval is annulled in the SAME canonical operation (actor, date and
        motive). The provider transaction of an Izipay payment is IMMUTABLE
        and is never touched.
        """
        aprobacion = (
            AprobacionPagoManual.objects
            .select_for_update()
            .filter(
                orden_pago_id=orden_pago.id,
                estado=EstadoAprobacionPagoManual.APROBADA,
            )
            .order_by("-created_at")
            .first()
        )
        if aprobacion is None:
            return

        aprobacion.estado = EstadoAprobacionPagoManual.ANULADA
        aprobacion.anulada_por_id = actor_id
        aprobacion.anulada_en = timezone.now()
        aprobacion.motivo_anulacion = motivo
        aprobacion.save(
            update_fields=[
                "estado",
                "anulada_por",
                "anulada_en",
                "motivo_anulacion",
                "updated_at",
            ]
        )
