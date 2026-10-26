"""
CrearAsignacionesFlujo — async flow for creating AsignacionCupo after payment confirmation.

Called after ConfirmarPagoFlujo marks Compra=PAGADA.
This flow creates AsignacionCupo entries for all registered personas.

Flow:
1. Lock the Compra and read its inscripcion
2. Allocate the paid capacity to the preregistered participants through
   AsignacionCoreService.asignar_cupos_a_preregistrados() — deterministic order
   and idempotent (a repeated call creates nothing new)
3. Sync AcreditacionEvento for each affected person

IMPORTANT: This does NOT create empty rows. AsignacionCupo is created only when
a registered person is actually assigned a paid spot, and never beyond the paid
capacity of the compra.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService

logger = logging.getLogger(__name__)


class CrearAsignacionesFlujo:
    """
    Async flow for creating AsignacionCupo after payment confirmation.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    async def _crear_asignaciones_por_compra(
        self,
        compra_id: str,
    ) -> list[dict]:
        """
        Create AsignacionCupo entries for all registered personas after payment.

        Steps:
        1. Get the Compra and its inscripcion
        2. Calculate available saldo
        3. Get registered personas without active asignacion
        4. Create asignaciones for up to disponible count
        5. Sync AcreditacionEvento for each affected person
        """
        return await sync_to_async(self._crear_asignaciones_sync)(compra_id)

    @transaction.atomic()
    def _crear_asignaciones_sync(self, compra_id: str) -> list[dict]:
        """
        Sync version with transaction.atomic for safe concurrent creation.

        The allocation itself is delegated to AsignacionCoreService, which owns
        the deterministic rules (order, capacity source, idempotency). This
        flow only orchestrates: allocate → sync acreditacion for each person.
        """
        from modules.commerce.domain.models import Compra
        from modules.salesianos_fest.domain.models import CompraInscripcion

        # Lock the commerce.Compra to prevent concurrent over-allocation
        compra = (
            Compra.objects
            .select_related("compra_inscripcion", "compra_inscripcion__inscripcion__evento")
            .select_for_update()
            .filter(id=compra_id)
            .first()
        )

        if compra is None:
            logger.warning(f"Compra {compra_id} not found for crear asignaciones")
            return []

        if compra.estado != EstadoCompraChoices.PAGADA:
            logger.info(f"Compra {compra_id} is not PAGADA, skipping asignaciones")
            return []

        compra_inscripcion = CompraInscripcion.objects.filter(
            compra_id=compra.id,
        ).select_related("inscripcion", "inscripcion__evento").first()

        if compra_inscripcion is None:
            logger.info(f"Compra {compra_id} is not linked to an inscripcion, skipping")
            return []

        inscripcion_id = str(compra_inscripcion.inscripcion_id)
        evento_id = str(compra_inscripcion.inscripcion.evento_id)

        # Deterministic + idempotent allocation of the paid capacity.
        asignaciones = self.asignacion_core.asignar_cupos_a_preregistrados(
            inscripcion_id=inscripcion_id,
            compra_preferida_id=str(compra.id),
        )

        resultados = []
        for asignacion in asignaciones:
            persona_id = str(asignacion.inscripcion_persona.persona_id)
            resultados.append({
                "asignacion_id": str(asignacion.id),
                "persona_id": persona_id,
                "inscripcion_id": inscripcion_id,
            })

            # Sync acreditacion for this person
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=persona_id,
            )

        logger.info(f"Created {len(resultados)} asignaciones for compra {compra_id}")
        return resultados
