"""
AgregarParticipanteFlujo — async flow for adding a participant to an existing team.

Async flow with transaction.atomic — validates and adds a single participant.
"""

import asyncio

from django.db import transaction
from injector import inject

from modules.inscripciones.domain.models import (
    EquipoInscrito,
    Inscripcion,
    Paquete,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.participacion_service import ParticipacionService
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.services.core import validators


class AgregarParticipanteFlujo:
    """
    Async flow for adding a participant to an existing team.

    Validates:
    - R11: person not already in this discipline+event
    - Package capacity not exceeded
    - Equipo↔discipline consistency
    """

    @inject
    def __init__(
        self,
        participacion_svc: ParticipacionService,
        participante_svc: ParticipanteService,
        equipo_svc: EquipoService,
    ):
        self.participacion_svc = participacion_svc
        self.participante_svc = participante_svc
        self.equipo_svc = equipo_svc

    async def _agregar_participante(
        self,
        equipo_id: str,
        persona_id: str,
        rol: str = "JUGADOR",
        talle_camiseta: str | None = None,
        notas: str | None = None,
        acepto_bases: bool | None = None,
        acepto_aptitud_fisica: bool | None = None,
        acepto_imagen: bool | None = None,
    ):
        """
        Add a participant to an existing equipo.

        Args:
            equipo_id: UUID of the equipo.
            persona_id: UUID of the persona.
            rol: Participant role (default JUGADOR).
            talle_camiseta: Optional shirt size.
            notas: Optional notes from the responsible.
            acepto_bases: Whether the participant accepted the event bases.
            acepto_aptitud_fisica: Whether the participant accepted the fitness certificate.
            acepto_imagen: Whether the participant consented to image usage.

        Raises:
            EquipoNotFoundError: If equipo not found.
            ParticipacionDuplicadaError: If R11 violation.
            CupoExcedidoError: If package capacity would be exceeded.
            ConsistenciaEquipoError: If team consistency check fails.
        """
        return await asyncio.to_thread(
            self._agregar_participante_sync,
            equipo_id=equipo_id,
            persona_id=persona_id,
            rol=rol,
            talle_camiseta=talle_camiseta,
            notas=notas,
            acepto_bases=acepto_bases,
            acepto_aptitud_fisica=acepto_aptitud_fisica,
            acepto_imagen=acepto_imagen,
        )

    @transaction.atomic()
    def _agregar_participante_sync(
        self,
        equipo_id: str,
        persona_id: str,
        rol: str = "JUGADOR",
        talle_camiseta: str | None = None,
        notas: str | None = None,
        acepto_bases: bool | None = None,
        acepto_aptitud_fisica: bool | None = None,
        acepto_imagen: bool | None = None,
    ):
        """
        Sync version wrapped in transaction.atomic.
        """
        # Get equipo and validate it exists
        equipo = self.equipo_svc.obtener(equipo_id)
        if equipo is None:
            raise exc.EquipoNotFoundError(f"Equipo {equipo_id} no encontrado.")

        inscripcion = equipo.inscripcion
        paquete = inscripcion.paquete
        evento_id = str(inscripcion.evento_id)
        disciplina_id = str(equipo.disciplina_id)

        # Validate discipline is in package
        if not validators.validar_disciplina_en_paquete(paquete, disciplina_id):
            raise exc.DisciplinaNoEnPaqueteError(
                f"La disciplina {disciplina_id} no está incluida en el paquete."
            )

        # Validate package capacity BEFORE adding (Nivel 2)
        capacidad_errors = validators.validar_cupo_paquete(inscripcion, paquete)
        if capacidad_errors:
            from modules.inscripciones.domain.models import ParticipacionDisciplina
            persona_ya_esta = ParticipacionDisciplina.objects.filter(
                equipo__inscripcion=inscripcion,
                persona_id=persona_id,
            ).exists()
            if not persona_ya_esta:
                raise exc.CupoExcedidoError("; ".join(capacidad_errors))

        # Create ParticipacionDisciplina (validates R11 and consistency internally)
        from modules.inscripciones.domain.schemas import ParticipacionCreateData
        participacion = self.participacion_svc.crear(ParticipacionCreateData(
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            persona_id=persona_id,
            equipo_id=equipo_id,
        ))

        # Create ParticipanteInscripcion
        from modules.inscripciones.domain.schemas import ParticipanteCreateData
        resultado = self.participante_svc.crear(ParticipanteCreateData(
            participacion_id=str(participacion.id),
            equipo_id=equipo_id,
            rol=rol,
            talle_camiseta=talle_camiseta,
            notas=notas,
        ))

        # Update Persona boolean acceptance fields and insurance fields
        if acepto_bases is not None or acepto_aptitud_fisica is not None or acepto_imagen is not None:
            from modules.usuarios.domain.models import Persona
            persona = Persona.objects.filter(id=persona_id).first()
            if persona:
                if acepto_bases is not None:
                    persona.acepto_bases = acepto_bases
                if acepto_aptitud_fisica is not None:
                    persona.acepto_aptitud_fisica = acepto_aptitud_fisica
                if acepto_imagen is not None:
                    persona.acepto_imagen = acepto_imagen
                persona.save(update_fields=["acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"])

        return resultado
