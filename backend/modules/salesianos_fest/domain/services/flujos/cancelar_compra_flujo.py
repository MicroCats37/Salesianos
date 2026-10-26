"""
CancelarCompraFlujo — async flow for cancelling a Compra (refund / abandoned payment).

Called when:
- The payment of a Compra is refunded
- A pending Compra is abandoned by the buyer

Flow:
1. Lock the commerce.Compra (SELECT FOR UPDATE) — safe against concurrent refunds
2. Mark the Compra as CANCELADA (idempotent: an already cancelled Compra is a no-op)
3. Revoke ONLY the ACTIVA AsignacionCupo derived from that Compra — assignments
   funded by other compras keep their right
4. Retire the Participacion that was backed by a revoked right (a revoked right
   cannot back an active participation)
5. Recalculate AcreditacionEvento for every affected persona, considering ALL
   their inscriptions (R10 — the person may still have access elsewhere)
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.exceptions import CompraNotFoundError
from modules.salesianos_fest.domain.results.compra_results import CompraCanceladaResult
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService

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
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    async def _cancelar_compra(self, compra_id: str) -> CompraCanceladaResult:
        """Cancel a Compra and revoke the rights derived from it."""
        return await sync_to_async(self._cancelar_sync)(compra_id)

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
                "compra_inscripcion",
                "compra_inscripcion__inscripcion__evento",
            )
            .select_for_update()
            .filter(id=compra_id)
            .first()
        )
        if compra is None:
            raise CompraNotFoundError()

        compra_inscripcion = getattr(compra, "compra_inscripcion", None)
        inscripcion_id = str(compra_inscripcion.inscripcion_id) if compra_inscripcion else ""

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

        # Recalculate the rights of every affected persona (all inscriptions)
        for persona_id, evento_id in personas_afectadas.items():
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=persona_id,
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
