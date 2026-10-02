"""
ParticipanteService — sync operations for ParticipanteInscripcion.

Core service — no transaction.atomic own, no async.
Validates Nivel 1 (roster min/max) when confirming/closing.
"""

from injector import inject

from modules.inscripciones.domain.models import (
    ParticipanteInscripcion,
    ParticipacionDisciplina,
    EquipoInscrito,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core import validators


class ParticipanteService:
    """
    Core service for ParticipanteInscripcion operations.
    """

    @inject
    def __init__(self):
        pass

    def crear(self, data) -> ParticipanteInscripcion:
        """
        Create a new ParticipanteInscripcion linked to a participacion.

        Does NOT validate roster min/max at creation time (draft mode).
        Roster validation happens at submit/confirm time via validar_roster_equipo.
        """
        return ParticipanteInscripcion.objects.create(
            participacion_id=data.participacion_id,
            equipo_id=data.equipo_id,
            rol=data.rol,
            talle_camiseta=data.talle_camiseta,
        )

    def actualizar(self, participante: ParticipanteInscripcion, data) -> ParticipanteInscripcion:
        """Update rol, talle_camiseta, and aseguradora fields of a ParticipanteInscripcion."""
        update_fields = data.model_dump(exclude_none=True)
        # Exclude aceptaciones — it is handled separately in the flujo
        update_fields.pop("aceptaciones", None)
        for field, value in update_fields.items():
            setattr(participante, field, value)
        participante.save()
        return participante

    def obtener(self, participante_id: str) -> ParticipanteInscripcion | None:
        """Get a ParticipanteInscripcion by ID."""
        return ParticipanteInscripcion.objects.filter(id=participante_id).first()

    def listar_por_equipo(self, equipo_id: str) -> list[ParticipanteInscripcion]:
        """List all participantes for an equipo."""
        return list(
            ParticipanteInscripcion.objects
            .filter(equipo_id=equipo_id)
            .select_related("participacion", "participacion__persona")
            .order_by("participacion__persona__apellidos")
        )

    def validar_roster_equipos_de_inscripcion(
        self,
        inscripcion_id: str,
    ) -> dict[str, list[str]]:
        """
        Validate roster limits for all equipos of an inscription.

        Called when submitting/confirming an inscription.

        Returns:
            Dict mapping equipo_id to list of error messages.
            Empty dict means all valid.
        """
        equipos = EquipoInscrito.objects.filter(inscripcion_id=inscripcion_id)
        errors_by_equipo = {}

        for equipo in equipos:
            disciplina = equipo.disciplina
            cantidad = equipo.participaciones.count()
            roster_errors = validators.validar_roster_equipo(disciplina, cantidad)
            if roster_errors:
                errors_by_equipo[str(equipo.id)] = roster_errors

        return errors_by_equipo

    def validar_roster_equipo_por_id(self, equipo_id: str) -> list[str]:
        """
        Validate roster limits for a single equipo.

        Returns:
            List of error messages (empty if valid).
        """
        equipo = EquipoInscrito.objects.filter(id=equipo_id).first()
        if equipo is None:
            return [f"Equipo {equipo_id} no encontrado."]
        disciplina = equipo.disciplina
        cantidad = equipo.participaciones.count()
        return validators.validar_roster_equipo(disciplina, cantidad)
