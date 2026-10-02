"""
ParticipanteAccionFlujo — async flow for participant edit/remove/move operations.

Async flow with transaction.atomic — handles:
- Editing participant rol/talle_camiseta
- Removing a participant from a team
- Moving a participant between equipos (same or different discipline)
"""

import asyncio

from django.db import transaction
from injector import inject

from modules.inscripciones.domain.models import (
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.services.core.participacion_service import ParticipacionService
from modules.inscripciones.domain.services.core import validators


class ParticipanteAccionFlujo:
    """
    Async flow for participant edit/remove/move operations.

    Validates ownership, R11, roster limits, and package capacity as appropriate.
    """

    @inject
    def __init__(
        self,
        participante_svc: ParticipanteService,
        equipo_svc: EquipoService,
        participacion_svc: ParticipacionService,
    ):
        self.participante_svc = participante_svc
        self.equipo_svc = equipo_svc
        self.participacion_svc = participacion_svc

    async def _editar_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
        rol: str | None = None,
        talle_camiseta: str | None = None,
        aseguradora_nombre: str | None = None,
        aseguradora_numero_poliza: str | None = None,
        notas: str | None = None,
    ):
        """
        Edit a participant's rol, talle_camiseta, insurance, and/or notes.

        Args:
            inscripcion_id: UUID of the inscription (for ownership validation).
            participante_id: UUID of the ParticipanteInscripcion.
            rol: New rol value (optional).
            talle_camiseta: New talle_camiseta value (optional).
            aseguradora_nombre: New aseguradora_nombre value (optional).
            aseguradora_numero_poliza: New aseguradora_numero_poliza value (optional).
            notas: New notas value (optional).

        Returns:
            Updated ParticipanteInscripcion.

        Raises:
            NotFoundError: If participante not found or doesn't belong to inscription.
            BusinessError: If user is not the inscription responsible.
        """
        return await asyncio.to_thread(
            self._editar_participante_sync,
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            rol=rol,
            talle_camiseta=talle_camiseta,
            aseguradora_nombre=aseguradora_nombre,
            aseguradora_numero_poliza=aseguradora_numero_poliza,
            notas=notas,
        )

    @transaction.atomic()
    def _editar_participante_sync(
        self,
        inscripcion_id: str,
        participante_id: str,
        rol: str | None = None,
        talle_camiseta: str | None = None,
        aseguradora_nombre: str | None = None,
        aseguradora_numero_poliza: str | None = None,
        notas: str | None = None,
    ):
        """
        Sync version wrapped in transaction.atomic.
        """
        from modules.inscripciones.domain.schemas import ParticipanteUpdateData

        participante = self.participante_svc.obtener(participante_id)
        if participante is None:
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"Participante {participante_id} no encontrado",
            )

        # Validate participant belongs to inscription
        equipo = participante.equipo
        if str(equipo.inscripcion_id) != str(inscripcion_id):
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"El participante {participante_id} no pertenece a la inscripción {inscripcion_id}",
            )

        # Update fields
        data = ParticipanteUpdateData(
            rol=rol,
            talle_camiseta=talle_camiseta,
            notas=notas,
        )
        resultado = self.participante_svc.actualizar(participante, data)

        # Update Persona insurance fields if any are provided
        if aseguradora_nombre is not None or aseguradora_numero_poliza is not None:
            persona = participante.participacion.persona
            if aseguradora_nombre is not None:
                persona.aseguradora_nombre = aseguradora_nombre
            if aseguradora_numero_poliza is not None:
                persona.aseguradora_numero_poliza = aseguradora_numero_poliza
            persona.save(update_fields=["aseguradora_nombre", "aseguradora_numero_poliza"])

        return resultado

    async def _remover_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
    ):
        """
        Remove a participant from a team.

        Deletes the ParticipanteInscripcion. If the associated ParticipacionDisciplina
        has no other ParticipanteInscripcion links, deletes the ParticipacionDisciplina too
        (unless it would violate domain constraints).

        Does NOT enforce min_jugadores on delete — draft workflows should not be blocked
        by minimum roster requirements.

        Args:
            inscripcion_id: UUID of the inscription (for ownership validation).
            participante_id: UUID of the ParticipanteInscripcion to remove.

        Raises:
            NotFoundError: If participante not found or doesn't belong to inscription.
            BusinessError: If user is not the inscription responsible.
        """
        return await asyncio.to_thread(
            self._remover_participante_sync,
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
        )

    @transaction.atomic()
    def _remover_participante_sync(
        self,
        inscripcion_id: str,
        participante_id: str,
    ):
        """
        Sync version wrapped in transaction.atomic.
        """
        participante = self.participante_svc.obtener(participante_id)
        if participante is None:
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"Participante {participante_id} no encontrado",
            )

        # Validate participant belongs to inscription
        equipo = participante.equipo
        if str(equipo.inscripcion_id) != str(inscripcion_id):
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"El participante {participante_id} no pertenece a la inscripción {inscripcion_id}",
            )

        participacion = participante.participacion
        participacion_id = participacion.id

        # Delete ParticipanteInscripcion
        participante.delete()

        # Check if ParticipacionDisciplina has other links
        otras_participaciones = ParticipanteInscripcion.objects.filter(
            participacion_id=participacion_id
        ).exists()

        if not otras_participaciones:
            # No other participants linked — safe to delete the ParticipacionDisciplina
            participacion.delete()

        return {"removed": True}

    async def _mover_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
        equipo_destino_id: str,
    ):
        """
        Move a participant to another equipo within the same inscription.

        - Same disciplina: update ParticipanteInscripcion.equipo_id to target team.
        - Different disciplina: atomically create/reuse ParticipacionDisciplina for
          (evento, target_disciplina, persona), update ParticipanteInscripcion to
          point to new participation/team, delete old ParticipacionDisciplina if orphaned.

        Args:
            inscripcion_id: UUID of the inscription (for ownership validation).
            participante_id: UUID of the ParticipanteInscripcion to move.
            equipo_destino_id: UUID of the target equipo.

        Returns:
            Updated ParticipanteInscripcion.

        Raises:
            NotFoundError: If participante, equipo destino, or inscription not found.
            ParticipacionDuplicadaError: If R11 would be violated (R11 duplicate).
            MaxJugadoresExcedidoError: If target equipo exceeds max_jugadores.
            CupoExcedidoError: If package capacity would be exceeded.
        """
        return await asyncio.to_thread(
            self._mover_participante_sync,
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            equipo_destino_id=equipo_destino_id,
        )

    @transaction.atomic()
    def _mover_participante_sync(
        self,
        inscripcion_id: str,
        participante_id: str,
        equipo_destino_id: str,
    ):
        """
        Sync version wrapped in transaction.atomic.
        """
        # Get source participante
        participante = self.participante_svc.obtener(participante_id)
        if participante is None:
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"Participante {participante_id} no encontrado",
            )

        # Validate source participant belongs to inscription
        equipo_origen = participante.equipo
        if str(equipo_origen.inscripcion_id) != str(inscripcion_id):
            raise exc.NotFoundError(
                resource="Participante",
                detail=f"El participante {participante_id} no pertenece a la inscripción {inscripcion_id}",
            )

        # Get target equipo
        equipo_destino = self.equipo_svc.obtener(equipo_destino_id)
        if equipo_destino is None:
            raise exc.EquipoNotFoundError(f"Equipo {equipo_destino_id} no encontrado.")

        # Validate target equipo belongs to same inscription
        if str(equipo_destino.inscripcion_id) != str(inscripcion_id):
            raise exc.BusinessError(
                "El equipo destino no pertenece a la misma inscripción."
            )

        # Get source and target discipline IDs
        disciplina_origen_id = str(equipo_origen.disciplina_id)
        disciplina_destino_id = str(equipo_destino.disciplina_id)
        misma_disciplina = disciplina_origen_id == disciplina_destino_id

        inscripcion = equipo_origen.inscripcion
        evento_id = str(inscripcion.evento_id)
        paquete = inscripcion.paquete

        # Get persona from participacion
        persona_id = str(participante.participacion.persona_id)

        if misma_disciplina:
            # ── Same discipline: just update equipo_id ──────────────────────────
            disciplina = equipo_destino.disciplina
            cantidad_destino = equipo_destino.participaciones.count()
            max_jugadores = disciplina.max_jugadores

            if max_jugadores is not None and cantidad_destino >= max_jugadores:
                raise exc.MaxJugadoresExcedidoError(
                    f"El equipo destino no puede exceder {max_jugadores} jugadores."
                )

            # Update equipo reference
            participante.equipo_id = equipo_destino_id
            participante.save()

        else:
            # ── Different discipline: complex move ──────────────────────────────
            # Check R11 for target discipline
            if validators.validar_r11_prevent_duplicado(
                evento_id=evento_id,
                disciplina_id=disciplina_destino_id,
                persona_id=persona_id,
            ):
                raise exc.ParticipacionDuplicadaError(
                    f"La persona ya está registrada en esa disciplina en este evento."
                )

            # Validate discipline is in package
            if not validators.validar_disciplina_en_paquete(paquete, disciplina_destino_id):
                raise exc.DisciplinaNoEnPaqueteError(
                    f"La disciplina {disciplina_destino_id} no está incluida en el paquete."
                )

            # Validate package capacity
            capacidad_errors = validators.validar_cupo_paquete(inscripcion, paquete)
            if capacidad_errors:
                persona_ya_esta = ParticipacionDisciplina.objects.filter(
                    equipo__inscripcion=inscripcion,
                    persona_id=persona_id,
                ).exists()
                if not persona_ya_esta:
                    raise exc.CupoExcedidoError("; ".join(capacidad_errors))

            # Validate max_jugadores on target equipo
            disciplina_destino = equipo_destino.disciplina
            cantidad_destino = equipo_destino.participaciones.count()
            max_jugadores_destino = disciplina_destino.max_jugadores

            if max_jugadores_destino is not None and cantidad_destino >= max_jugadores_destino:
                raise exc.MaxJugadoresExcedidoError(
                    f"El equipo destino no puede exceder {max_jugadores_destino} jugadores."
                )

            # Find or create ParticipacionDisciplina for (evento, disciplina_destino, persona)
            from modules.inscripciones.domain.schemas import ParticipacionCreateData
            participacion_existente = ParticipacionDisciplina.objects.filter(
                evento_id=evento_id,
                disciplina_id=disciplina_destino_id,
                persona_id=persona_id,
            ).first()

            if participacion_existente:
                participacion_nueva = participacion_existente
            else:
                participacion_nueva = self.participacion_svc.crear(ParticipacionCreateData(
                    evento_id=evento_id,
                    disciplina_id=disciplina_destino_id,
                    persona_id=persona_id,
                    equipo_id=equipo_destino_id,
                ))

            # Save old participacion id BEFORE updating
            participacion_anterior_id = str(participante.participacion_id)

            # Update participante to point to new participation and equipo
            participante.participacion_id = participacion_nueva.id
            participante.equipo_id = equipo_destino_id
            participante.save()

            # Clean up old ParticipacionDisciplina if orphaned
            otras_participaciones = ParticipanteInscripcion.objects.filter(
                participacion_id=participacion_anterior_id
            ).exclude(id=participante.id).exists()

            if not otras_participaciones:
                # No other participants linked to old participation — delete it
                ParticipacionDisciplina.objects.filter(id=participacion_anterior_id).delete()

        return participante
