"""`InscripcionSelector` — consultas de SOLO LECTURA de inscripciones y equipos.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)
"""

from django.db.models import QuerySet

from modules.salesianos_fest.domain.models import Equipo, Inscripcion


class InscripcionSelector:
    """Consultas de solo lectura sobre `Inscripcion` y `Equipo`."""

    def obtener_por_id(self, inscripcion_id) -> Inscripcion | None:
        """La inscripción con ese identificador, o `None`."""
        return (
            Inscripcion.objects.filter(id=inscripcion_id)
            .select_related(
                "edicion",
                "responsable",
                "paquete",
                "promocion",
                "fusion_promocion",
            )
            .first()
        )

    def obtener_por_responsable_y_paquete(
        self,
        edicion_id,
        responsable_id,
        paquete_id,
    ) -> Inscripcion | None:
        """La inscripción viva de ese responsable con ese paquete, o `None`.

        Es la consulta de REUTILIZACIÓN: un reintento del alta debe devolver
        la inscripción que ya existe, no crear una segunda.
        """
        return (
            Inscripcion.objects.filter(
                edicion_id=edicion_id,
                responsable_id=responsable_id,
                paquete_id=paquete_id,
            )
            .exclude(estado="CANCELADA")
            .select_related(
                "edicion",
                "responsable",
                "paquete",
                "promocion",
                "fusion_promocion",
            )
            .first()
        )

    def listar_equipos(self, inscripcion_id) -> QuerySet[Equipo]:
        """Los equipos de una inscripción, en orden estable."""
        return (
            Equipo.objects.filter(inscripcion_id=inscripcion_id)
            .select_related("disciplina", "categoria")
            .order_by("nombre")
        )

    def obtener_equipo(self, inscripcion_id, equipo_id) -> Equipo | None:
        """El equipo indicado DENTRO de la inscripción, o `None`.

        Es la consulta de AISLAMIENTO: un equipo de otra inscripción NO
        existe para esta inscripción (`RN-E01`, `RN-I05`).
        """
        return (
            Equipo.objects.filter(id=equipo_id, inscripcion_id=inscripcion_id)
            .select_related("disciplina", "categoria")
            .first()
        )


__all__ = ["InscripcionSelector"]
