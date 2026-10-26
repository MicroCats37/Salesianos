"""EquipoSelector — read-only queries for equipos."""
from typing import Optional

from ..models import Equipo
from ..results.inscripcion_results import EquipoResult


class EquipoSelector:
    """Queries for Equipo entities."""

    @staticmethod
    def get_by_id(equipo_id: str) -> Optional[EquipoResult]:
        """Return an equipo by ID or None."""
        try:
            eq = Equipo.objects.select_related(
                "inscripcion__evento",
                "disciplina",
                "categoria",
            ).get(id=equipo_id)
            return EquipoResult(
                id=str(eq.id),
                inscripcion_id=str(eq.inscripcion_id),
                disciplina_id=str(eq.disciplina_id),
                disciplina_nombre=eq.disciplina.nombre,
                disciplina_sigla=eq.disciplina.sigla,
                categoria_id=str(eq.categoria_id) if eq.categoria_id else None,
                categoria_nombre=eq.categoria.nombre if eq.categoria_id else None,
                nombre=eq.nombre,
                estado=eq.estado,
                created_at=eq.created_at,
            )
        except Equipo.DoesNotExist:
            return None

    @staticmethod
    def get_by_inscripcion(inscripcion_id: str) -> list[EquipoResult]:
        """Return all equipos for an inscripcion."""
        qs = Equipo.objects.select_related(
            "disciplina", "categoria",
        ).filter(inscripcion_id=inscripcion_id).order_by("nombre")
        return [
            EquipoResult(
                id=str(eq.id),
                inscripcion_id=str(eq.inscripcion_id),
                disciplina_id=str(eq.disciplina_id),
                disciplina_nombre=eq.disciplina.nombre,
                disciplina_sigla=eq.disciplina.sigla,
                categoria_id=str(eq.categoria_id) if eq.categoria_id else None,
                categoria_nombre=eq.categoria.nombre if eq.categoria_id else None,
                nombre=eq.nombre,
                estado=eq.estado,
                created_at=eq.created_at,
            )
            for eq in qs
        ]
