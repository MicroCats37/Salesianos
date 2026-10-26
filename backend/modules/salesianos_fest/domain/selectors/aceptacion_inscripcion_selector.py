"""
AceptacionInscripcionSelector — read-only queries for the legal acceptances.

The legal acceptances (BASES / APTITUD_FISICA / IMAGEN) had NO query surface
until now. The operational administration surface must be able to answer "who
has not accepted the bases?", and the acceptances belong to THIS module.

Read-only by construction: no method in this selector writes.
"""
from django.db.models import QuerySet

from modules.salesianos_fest.domain.constants import EstadoInscripcionPersonaChoices
from modules.salesianos_fest.domain.models import (
    AceptacionInscripcion,
    InscripcionPersona,
)


class AceptacionInscripcionSelector:
    """Read-only queries for AceptacionInscripcion."""

    def obtener_por_id(self, aceptacion_id: str) -> AceptacionInscripcion | None:
        """Return the acceptance with the given id, or None."""
        return (
            AceptacionInscripcion.objects
            .select_related(
                "inscripcion_persona__persona",
                "inscripcion_persona__inscripcion",
            )
            .filter(id=aceptacion_id)
            .first()
        )

    def listar_por_inscripcion(
        self,
        inscripcion_id: str,
    ) -> QuerySet[AceptacionInscripcion]:
        """Return the acceptances registered for one inscription."""
        return (
            AceptacionInscripcion.objects
            .filter(inscripcion_persona__inscripcion_id=inscripcion_id)
            .select_related("inscripcion_persona__persona")
            .order_by("inscripcion_persona_id", "tipo_aceptacion")
        )

    def listar_por_evento(self, evento_id: str) -> QuerySet[AceptacionInscripcion]:
        """Return the acceptances registered in an event."""
        return (
            AceptacionInscripcion.objects
            .filter(inscripcion_persona__inscripcion__evento_id=evento_id)
            .select_related(
                "inscripcion_persona__persona",
                "inscripcion_persona__inscripcion",
            )
            .order_by("inscripcion_persona_id", "tipo_aceptacion")
        )

    def listar_pendientes_por_evento(
        self,
        evento_id: str,
    ) -> QuerySet[InscripcionPersona]:
        """Return the active roster members of an event with NO acceptance.

        The event scope travels through `inscripcion_persona__inscripcion__evento`:
        an acceptance belongs to the event of the inscription it was given in.
        """
        aceptados_ids = (
            AceptacionInscripcion.objects
            .filter(inscripcion_persona__inscripcion__evento_id=evento_id)
            .values_list("inscripcion_persona_id", flat=True)
        )

        return (
            InscripcionPersona.objects
            .filter(
                inscripcion__evento_id=evento_id,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
            .exclude(id__in=aceptados_ids)
            .select_related("persona", "inscripcion")
            .order_by("inscripcion_id", "persona__nombres", "persona__apellidos")
        )
