"""
AsignacionSelector — query interface for AsignacionCupo.
"""
from modules.salesianos_fest.domain.models import AsignacionCupo


class AsignacionSelector:
    """Query interface for AsignacionCupo."""

    def obtener_por_id(self, asignacion_id: str) -> AsignacionCupo | None:
        """Get an AsignacionCupo by its ID with select_related."""
        return (
            AsignacionCupo.objects
            .select_related("inscripcion", "compra", "inscripcion_persona", "inscripcion_persona__persona")
            .filter(id=asignacion_id)
            .first()
        )

    def listar_por_inscripcion(self, inscripcion_id: str) -> list[AsignacionCupo]:
        """List all asignaciones for an inscripcion."""
        return list(
            AsignacionCupo.objects
            .select_related("compra", "inscripcion_persona", "inscripcion_persona__persona")
            .filter(inscripcion_id=inscripcion_id)
            .order_by("-created_at")
        )

    def listar_activas_por_compra(self, compra_id: str) -> list[AsignacionCupo]:
        """List all active asignaciones for a compra."""
        return list(
            AsignacionCupo.objects
            .select_related("inscripcion_persona", "inscripcion_persona__persona")
            .filter(compra_id=compra_id, estado="ACTIVA")
            .order_by("created_at")
        )
