"""
CambiarEstadoInscripcionFlujo — async flow for changing inscription state.

Async flow with transaction.atomic — validates roster limits when confirming/closing.
"""

import asyncio

from django.db import transaction
from injector import inject

from modules.inscripciones.domain.models import Inscripcion
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.constants import EstadoInscripcionChoices


class CambiarEstadoInscripcionFlujo:
    """
    Async flow for changing the state of an inscription.

    When transitioning to VALIDADA or CONFIRMADA, validates:
    - All teams meet discipline roster min/max limits (Nivel 1)
    """

    @inject
    def __init__(
        self,
        inscripcion_svc: InscripcionService,
        participante_svc: ParticipanteService,
    ):
        self.inscripcion_svc = inscripcion_svc
        self.participante_svc = participante_svc

    async def _cambiar_estado(
        self,
        inscripcion_id: str,
        nuevo_estado: str,
        observacion: str | None = None,
    ) -> Inscripcion:
        """
        Change the state of an inscription.

        Args:
            inscripcion_id: UUID of the inscription.
            nuevo_estado: New estado value.
            observacion: Optional observation.

        Returns:
            The updated Inscripcion.

        Raises:
            InscripcionNotFoundError: If inscription not found.
            BusinessError: If roster validation fails when confirming.
        """
        return await asyncio.to_thread(
            self._cambiar_estado_sync,
            inscripcion_id=inscripcion_id,
            nuevo_estado=nuevo_estado,
            observacion=observacion,
        )

    @transaction.atomic()
    def _cambiar_estado_sync(
        self,
        inscripcion_id: str,
        nuevo_estado: str,
        observacion: str | None = None,
    ) -> Inscripcion:
        """
        Sync version wrapped in transaction.atomic.
        """
        inscripcion = self.inscripcion_svc.obtener(inscripcion_id)
        if inscripcion is None:
            raise exc.InscripcionNotFoundError(f"Inscripcion {inscripcion_id} no encontrada.")

        # Validate roster limits when confirming or validating
        if nuevo_estado in (EstadoInscripcionChoices.VALIDADA, EstadoInscripcionChoices.CONFIRMADA):
            roster_errors = self.participante_svc.validar_roster_equipos_de_inscripcion(inscripcion_id)
            if roster_errors:
                error_msgs = []
                for eq_id, errors in roster_errors.items():
                    error_msgs.append(f"Equipo {eq_id}: {'; '.join(errors)}")
                raise exc.CupoEquipoError(
                    f"Hay equipos que no cumplen los límites de jugadores: {'; '.join(error_msgs)}"
                )

        return self.inscripcion_svc.actualizar_estado(
            inscripcion=inscripcion,
            nuevo_estado=nuevo_estado,
            observacion=observacion,
        )
