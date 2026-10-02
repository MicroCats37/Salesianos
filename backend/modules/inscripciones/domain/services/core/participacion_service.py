"""
ParticipacionService — sync operations for ParticipacionDisciplina.

Core service — no transaction.atomic own, no async.
Validates R11 (Capa 2) and equipo↔participacion consistency.
"""

from injector import inject

from modules.inscripciones.domain.models import (
    ParticipacionDisciplina,
    EquipoInscrito,
    Disciplina,
    Paquete,
    Inscripcion,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core import validators


class ParticipacionService:
    """
    Core service for ParticipacionDisciplina operations.

    Handles the R11 protection (Capa 2 pre-check) and equipo↔participacion consistency.
    The UniqueConstraint on the model provides Capa 1 (DB-level protection).
    """

    @inject
    def __init__(self):
        pass

    def crear(self, data) -> ParticipacionDisciplina:
        """
        Create a new ParticipacionDisciplina.

        Validations applied (in order):
        1. R11 pre-check: persona not already in disciplina+evento (Capa 2)
        2. Equipo↔participacion consistency (Capa 3)
        3. Package capacity check (Nivel 2)

        The DB constraint (Capa 1) is the final fallback for race conditions.
        """
        # ── Validation Capa 2: R11 pre-check ────────────────────────────────
        if validators.validar_r11_prevent_duplicado(
            evento_id=data.evento_id,
            disciplina_id=data.disciplina_id,
            persona_id=data.persona_id,
        ):
            raise exc.ParticipacionDuplicadaError(
                "La persona ya está registrada en esta disciplina en este evento."
            )

        # ── Validation Capa 3: equipo↔participacion consistency ─────────────
        equipo = EquipoInscrito.objects.filter(id=data.equipo_id).first()
        if equipo is None:
            raise exc.EquipoNotFoundError(f"Equipo {data.equipo_id} no encontrado.")

        consistencia_errors = validators.validar_consistencia_equipo_participacion(
            equipo=equipo,
            evento_id=data.evento_id,
            disciplina_id=data.disciplina_id,
        )
        if consistencia_errors:
            raise exc.ConsistenciaEquipoError("; ".join(consistencia_errors))

        # ── Validation Nivel 2: package capacity ─────────────────────────────
        inscripcion = equipo.inscripcion
        paquete = inscripcion.paquete
        capacidad_errors = validators.validar_cupo_paquete(inscripcion, paquete)
        if capacidad_errors:
            raise exc.CupoExcedidoError("; ".join(capacidad_errors))

        # ── Create ───────────────────────────────────────────────────────────
        return ParticipacionDisciplina.objects.create(
            evento_id=data.evento_id,
            disciplina_id=data.disciplina_id,
            persona_id=data.persona_id,
            equipo_id=data.equipo_id,
        )

    def obtener(self, participacion_id: str) -> ParticipacionDisciplina | None:
        """Get a ParticipacionDisciplina by ID."""
        return ParticipacionDisciplina.objects.filter(id=participacion_id).first()

    def listar_por_evento(self, evento_id: str) -> list[ParticipacionDisciplina]:
        """List all participaciones for an event."""
        return list(
            ParticipacionDisciplina.objects
            .filter(evento_id=evento_id)
            .select_related("persona", "disciplina", "equipo")
            .order_by("disciplina__nombre", "persona__apellidos")
        )

    def listar_por_persona(self, persona_id: str) -> list[ParticipacionDisciplina]:
        """List all participaciones for a person."""
        return list(
            ParticipacionDisciplina.objects
            .filter(persona_id=persona_id)
            .select_related("evento", "disciplina", "equipo")
            .order_by("-created_at")
        )

    def listar_por_equipo(self, equipo_id: str) -> list[ParticipacionDisciplina]:
        """List all participaciones for an equipo."""
        return list(
            ParticipacionDisciplina.objects
            .filter(equipo_id=equipo_id)
            .select_related("persona", "evento", "disciplina")
            .order_by("persona__apellidos")
        )
