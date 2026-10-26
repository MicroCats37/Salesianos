"""
LiberarCupoFlujo — async flow for releasing a player's cupo.

Called when:
- User wants to release the cupo of a player in an inscripcion
- The player keeps their AsignacionCupo in LIBERADA state (not deleted)

Flow (SPEC F5):
1. Validate admin/responsable permission
2. For each Participacion of the person in this inscripcion:
   a. Mark Participacion.estado = RETIRADA
3. If person has no more active participaciones in this inscripcion:
   a. Mark AsignacionCupo.estado = LIBERADA
4. Recalculate AcreditacionEvento for the person considering ALL inscriptions (R10)
5. The purchased quota is NOT returned; it remains available for reassignment

SPEC F5: Retirar a Juan de inscription A pero permanece en B

Multi-discipline rule (one paid cup, several disciplines):
`disciplina_id` scopes the release to ONE discipline. The cup is then liberated
ONLY when the person holds no other ACTIVE participation in the inscription —
while another discipline is still active the paid right must survive, because
the person is still playing with it. The check is evaluated BEFORE the rows are
retired: after the update it would always be False and the rule could never be
expressed.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.models import Participacion, Inscripcion
from modules.salesianos_fest.domain.exceptions import FechaLimiteExcedidaError

logger = logging.getLogger(__name__)


class LiberarCupoFlujo:
    """
    Async flow for liberating a player's cupo.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    def _verificar_fecha_limite(self, inscripcion_id: str) -> None:
        """Verify that modifications are still allowed for this evento."""
        inscripcion = Inscripcion.objects.select_related("evento").get(id=inscripcion_id)
        if not inscripcion.evento.puede_modificar():
            raise FechaLimiteExcedidaError()

    async def _liberar_cupo(
        self,
        inscripcion_id: str,
        persona_id: str,
        motivo: str | None = None,
        disciplina_id: str | None = None,
    ) -> dict:
        """
        Liberate a player's cupo from an inscripcion.

        Steps:
        1. Mark the Participacion(s) as RETIRADA — all of them in the
           inscripcion, or only the ones of `disciplina_id` when it is given.
        2. Evaluate whether the person still holds an ACTIVE participation in
           another discipline of this inscripcion (BEFORE retiring the rows).
        3. If no active participation is left, mark AsignacionCupo as LIBERADA.
        4. Recalculate AcreditacionEvento for this person across ALL inscriptions
        """
        return await sync_to_async(self._liberar_cupo_sync)(
            inscripcion_id, persona_id, motivo, disciplina_id
        )

    @transaction.atomic()
    def _liberar_cupo_sync(
        self,
        inscripcion_id: str,
        persona_id: str,
        motivo: str | None = None,
        disciplina_id: str | None = None,
    ) -> dict:
        """
        Sync version with transaction.atomic.
        """
        from modules.salesianos_fest.domain.constants import EstadoParticipacionChoices

        # Verify fecha_limite has not been exceeded
        self._verificar_fecha_limite(inscripcion_id)

        participaciones_activas = Participacion.objects.filter(
            inscripcion_persona__inscripcion_id=inscripcion_id,
            inscripcion_persona__persona_id=persona_id,
            estado=EstadoParticipacionChoices.ACTIVA,
        )

        if disciplina_id:
            a_retirar = participaciones_activas.filter(disciplina_id=disciplina_id)
            # The cup survives while the person still plays in ANOTHER
            # discipline of this inscripcion. Evaluated BEFORE the update.
            otras_participaciones = (
                participaciones_activas.exclude(disciplina_id=disciplina_id).exists()
            )
        else:
            a_retirar = participaciones_activas
            # The release is inscription-scoped: every participation of the
            # person in this inscripcion is retired, so none survives.
            otras_participaciones = False

        # Mark the participaciones as RETIRADA
        a_retirar.update(estado=EstadoParticipacionChoices.RETIRADA)

        resultado = {
            "inscripcion_id": inscripcion_id,
            "persona_id": persona_id,
            "participaciones_retiradas": True,
            "cupo_liberado": False,
            "asignacion_id": None,
        }

        # If no other active participation is left, liberate the cupo
        if not otras_participaciones:
            asignacion = self.asignacion_core.obtener_asignacion_activa_por_persona(
                inscripcion_id, persona_id
            )
            if asignacion:
                asignacion = self.asignacion_core.liberar_asignacion(asignacion, motivo)
                resultado["cupo_liberado"] = True
                resultado["asignacion_id"] = str(asignacion.id)

        # Recalculate AcreditacionEvento for this person across ALL inscriptions
        # (R10: Person may still have access via another inscription)
        evento_id = str(Inscripcion.objects.get(id=inscripcion_id).evento_id)
        self.acreditacion_core.sync_acreditacion_desde_compras(
            evento_id=evento_id,
            persona_id=persona_id,
        )

        return resultado
