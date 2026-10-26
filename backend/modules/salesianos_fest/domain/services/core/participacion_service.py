"""Core sync service for Participacion — no transaction.atomic itself."""
from typing import Optional

from modules.usuarios.domain.models.persona import Persona

from ...constants import EstadoParticipacionChoices
from ...models import Disciplina, Equipo, InscripcionPersona, Participacion
from ...schemas.inscripcion_schemas import ParticipacionCreateData, ParticipacionUpdateData
from ...exceptions import (
    ParticipacionNotFoundError,
    R11ViolationError,
    RosterCompletoError,
    DisciplinaNotFoundError,
    CupoNoAsignadoError,
    EquipoDeOtraInscripcionError,
    GeneroNoPermitidoError,
)
from ...validators import es_genero_compatible_con_modalidad


class ParticipacionCoreService:
    """Sync operations for Participacion — caller provides transaction.atomic."""

    def _tiene_cupo_activo(self, inscripcion_persona: InscripcionPersona) -> bool:
        """Check if the InscripcionPersona has an active AsignacionCupo."""
        from ...services.core.asignacion_service import AsignacionCoreService

        return (
            AsignacionCoreService()
            .obtener_asignacion_activa_por_inscripcion_persona(
                inscripcion_id=str(inscripcion_persona.inscripcion_id),
                inscripcion_persona_id=str(inscripcion_persona.id),
            )
            is not None
        )

    def _bloquear_y_validar_genero(self, disciplina_id, persona_id) -> None:
        """Lock the discipline and the person, then enforce the gender matrix.

        The lock order is ALWAYS discipline -> person, in every write path, so
        two concurrent operations can never deadlock waiting on the same two
        rows in the opposite order. The values read under the lock are the
        authoritative persisted ones: the redundant ``Participacion.disciplina``
        and ``Participacion.persona`` columns are only a denormalized copy of
        the same truth and are never used to decide compatibility.

        Raises:
            GeneroNoPermitidoError: when the pair (genero, modalidad) is not
                allowed by the compatibility matrix.
        """
        disciplina = Disciplina.objects.select_for_update().get(pk=disciplina_id)
        persona = Persona.objects.select_for_update().get(pk=persona_id)

        if not es_genero_compatible_con_modalidad(persona.genero, disciplina.modalidad):
            raise GeneroNoPermitidoError()

    def crear(self, data: ParticipacionCreateData) -> Participacion:
        """Create a participacion.

        Validation order (Phase 2):
          1. Inscription membership — implicit (InscripcionPersona belongs to this inscripcion)
          2. Active cup — _tiene_cupo_activo() via CupoNoAsignadoError
          3. R11 — no active participacion for same (evento, disciplina, persona)
          4. Roster — count of active participaciones < disciplina.max_jugadores
          5. Gender matrix — the (genero, modalidad) pair must be allowed

        Every check happens BEFORE the row is created, so a rejection leaves no
        trace: the caller wraps this in `transaction.atomic()` and the raised
        domain error rolls the whole operation back.

        Syncs redundant fields: evento, disciplina, persona from related objects.
        """
        # Get inscripcion_persona with related data
        ip = InscripcionPersona.objects.select_related(
            "inscripcion__evento",
            "persona",
        ).get(id=data.inscripcion_persona_id)

        # Get equipo with related data
        eq = Equipo.objects.select_related("disciplina", "inscripcion").get(id=data.equipo_id)

        # Sync redundant fields from related objects
        evento_id = str(ip.inscripcion.evento_id)
        disciplina_id = str(eq.disciplina_id)
        persona_id = str(ip.persona_id)

        # Active cup check: participant must have AsignacionCupo.ACTIVA
        if not self._tiene_cupo_activo(ip):
            raise CupoNoAsignadoError()

        # R11 check: any active participacion for same (evento, disciplina, persona)?
        existing = Participacion.objects.filter(
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            persona_id=persona_id,
            estado="A",
        ).exists()
        if existing:
            raise R11ViolationError()

        # Roster check: count active participaciones for this equipo
        active_count = Participacion.objects.filter(
            equipo_id=data.equipo_id,
            estado="A",
        ).count()
        if active_count >= eq.disciplina.max_jugadores:
            raise RosterCompletoError()

        # Gender matrix: the persisted gender must be compatible with the
        # persisted modality of the target discipline.
        self._bloquear_y_validar_genero(eq.disciplina_id, ip.persona_id)

        participacion = Participacion(
            inscripcion_persona_id=data.inscripcion_persona_id,
            equipo_id=data.equipo_id,
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            persona_id=persona_id,
            rol=data.rol,
            talla_camiseta=data.talla_camiseta,
            notas=data.notas,
            estado=data.estado,
        )
        participacion.save()
        return participacion

    def actualizar(self, participacion: Participacion, data: ParticipacionUpdateData) -> Participacion:
        """Update participacion fields (except redundant sync fields).

        A reactivation (``R`` -> ``A``) is an active creation in disguise: the
        row becomes visible to the roster again, so it must satisfy the gender
        matrix like any other active participation. Retirement (``A`` -> ``R``)
        is NEVER blocked — an incompatible legacy row must always be retirable.
        """
        update_fields = data.model_dump(exclude_none=True)
        estado_nuevo = update_fields.get("estado")
        es_reactivacion = (
            estado_nuevo == EstadoParticipacionChoices.ACTIVA
            and participacion.estado != EstadoParticipacionChoices.ACTIVA
        )

        if es_reactivacion:
            self._bloquear_y_validar_genero(
                participacion.disciplina_id,
                participacion.inscripcion_persona.persona_id,
            )

        for field, value in update_fields.items():
            setattr(participacion, field, value)
        participacion.save()
        return participacion

    def obtener_por_id(self, participacion_id: str) -> Participacion:
        """Get a participacion by ID or raise ParticipacionNotFoundError."""
        try:
            return Participacion.objects.get(id=participacion_id)
        except Participacion.DoesNotExist:
            raise ParticipacionNotFoundError()

    def mover(self, participacion: Participacion, equipo_destino_id: str) -> Participacion:
        """Move a participacion to another equipo.

        Validation order:
          1. Active cup — _tiene_cupo_activo() via CupoNoAsignadoError
          2. Destination team — it must belong to the SAME inscripcion
             (EquipoDeOtraInscripcionError)
          3. R11 — no OTHER active participacion for the same
             (evento, disciplina, persona) of the DESTINATION discipline
             (R11ViolationError)
          4. Roster — the destination equipo is not full (RosterCompletoError)
          5. Gender matrix — evaluated against the DESTINATION discipline

        The redundant fields `evento` and `disciplina` are re-synced from the
        destination team. They are the fields the R11 constraint reads, so a
        move across disciplines that left them stale would corrupt the row and
        silently bypass the R11 check.
        """
        # Verify active cup (must have cup to stay in any team)
        if not self._tiene_cupo_activo(participacion.inscripcion_persona):
            raise CupoNoAsignadoError()

        eq_destino = Equipo.objects.select_related(
            "disciplina", "inscripcion"
        ).get(id=equipo_destino_id)

        # The roster of an inscripcion is paid by the cupos of that SAME
        # inscripcion — a team of another inscripcion cannot host the row.
        inscripcion_origen_id = str(participacion.inscripcion_persona.inscripcion_id)
        if str(eq_destino.inscripcion_id) != inscripcion_origen_id:
            raise EquipoDeOtraInscripcionError()

        evento_destino_id = str(eq_destino.inscripcion.evento_id)
        disciplina_destino_id = str(eq_destino.disciplina_id)

        # R11 for the DESTINATION discipline — the row being moved is excluded.
        duplicada = (
            Participacion.objects.filter(
                evento_id=evento_destino_id,
                disciplina_id=disciplina_destino_id,
                persona_id=participacion.persona_id,
                estado="A",
            )
            .exclude(id=participacion.id)
            .exists()
        )
        if duplicada:
            raise R11ViolationError()

        # Roster check for destination equipo
        active_count = Participacion.objects.filter(
            equipo_id=equipo_destino_id,
            estado="A",
        ).count()
        if active_count >= eq_destino.disciplina.max_jugadores:
            raise RosterCompletoError()

        # Gender matrix: the move is evaluated against the DESTINATION
        # discipline — the source discipline is irrelevant once the row leaves
        # it.
        self._bloquear_y_validar_genero(
            eq_destino.disciplina_id,
            participacion.inscripcion_persona.persona_id,
        )

        participacion.equipo = eq_destino
        participacion.evento_id = evento_destino_id
        participacion.disciplina_id = disciplina_destino_id
        participacion.save()
        return participacion

    def retirer(self, participacion: Participacion) -> Participacion:
        """Retire a participacion (set estado=R).

        Retirement is NEVER blocked by the gender matrix: an incompatible
        legacy row must always be retirable, otherwise the data could not be
        remediated.
        """
        participacion.estado = EstadoParticipacionChoices.RETIRADA
        participacion.save()
        return participacion
