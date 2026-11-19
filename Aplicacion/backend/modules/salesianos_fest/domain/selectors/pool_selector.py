"""`PoolSelector` — consultas de SOLO LECTURA del pool de una inscripción.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector NO decide: sólo cuenta y lista. Las decisiones (qué cupo se
puede asignar, si la persona es elegible, si la activations ya se aplicó)
viven en los servicios.
"""

from django.db.models import QuerySet

from modules.salesianos_fest.domain.constants import EstadoParticipacion
from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    Participacion,
)


class PoolSelector:
    """Consultas de solo lectura sobre el pool y la capacidad."""

    def listar_participaciones(self, inscripcion_id) -> QuerySet[Participacion]:
        """Todas las participaciones de una inscripción, en orden estable.

        Incluye las retiradas: retirar NO es borrar y el historial de la
        plantilla es parte de la información de la inscripción (`RN-I04`).
        """
        return (
            Participacion.objects.filter(inscripcion_id=inscripcion_id)
            .select_related("persona", "equipo", "disciplina")
            .order_by("equipo_id", "created_at")
        )

    def obtener_participacion(self, participacion_id) -> Participacion | None:
        """La participación con ese identificador, o `None`."""
        return (
            Participacion.objects.filter(id=participacion_id)
            .select_related("inscripcion", "persona", "equipo", "disciplina")
            .first()
        )

    def obtener_participacion_activa(
        self,
        inscripcion_id,
        persona_id,
    ) -> Participacion | None:
        """La participación ACTIVA de esa persona en esa inscripción, o `None`."""
        return (
            Participacion.objects.filter(
                inscripcion_id=inscripcion_id,
                persona_id=persona_id,
                estado=EstadoParticipacion.ACTIVA,
            )
            .select_related("equipo", "disciplina")
            .first()
        )

    def obtener_participacion_activa_en_disciplina(
        self,
        edicion_id,
        disciplina_id,
        persona_id,
    ) -> Participacion | None:
        """La participación ACTIVA de esa persona en esa disciplina y edición.

        Es la consulta de SOLAPAMIENTO (`RN-I05`): una persona no puede
        participar activamente dos veces en la misma disciplina de la misma
        edición, ni siquiera desde otra inscripción.
        """
        return (
            Participacion.objects.filter(
                edicion_id=edicion_id,
                disciplina_id=disciplina_id,
                persona_id=persona_id,
                estado=EstadoParticipacion.ACTIVA,
            )
            .select_related("inscripcion")
            .first()
        )

    def contar_activas_por_equipo(self, equipo_id) -> int:
        """Cuántas participaciones ACTIVAS tiene el equipo."""
        return Participacion.objects.filter(
            equipo_id=equipo_id,
            estado=EstadoParticipacion.ACTIVA,
        ).count()

    def obtener_activacion_por_clave(self, clave) -> ActivacionCapacidad | None:
        """La activación de capacidad con esa clave, o `None`."""
        return ActivacionCapacidad.objects.filter(clave=clave).first()

    def listar_activaciones(self, inscripcion_id) -> QuerySet[ActivacionCapacidad]:
        """Las activaciones de capacidad de una inscripción, en orden estable."""
        return ActivacionCapacidad.objects.filter(
            inscripcion_id=inscripcion_id
        ).order_by("-aplicada_en")


__all__ = ["PoolSelector"]
