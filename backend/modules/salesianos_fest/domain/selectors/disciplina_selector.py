"""Disciplina selector — read-only queries for disciplinas."""
from typing import List

from ..models import Disciplina
from ..results.catalogo_results import DisciplinaResult


class DisciplinaSelector:
    """Queries for Disciplina entities."""

    @staticmethod
    def get_activas() -> List[DisciplinaResult]:
        """Return all active disciplinas."""
        qs = Disciplina.objects.filter(esta_activa=True).order_by("nombre")
        return [
            DisciplinaResult(
                id=str(d.id),
                nombre=d.nombre,
                sigla=d.sigla,
                modalidad=d.modalidad,
                min_jugadores=d.min_jugadores,
                max_jugadores=d.max_jugadores,
            )
            for d in qs
        ]

    @staticmethod
    def get_by_id(disciplina_id: str) -> DisciplinaResult | None:
        """Return a disciplina by ID or None."""
        try:
            d = Disciplina.objects.get(id=disciplina_id)
            return DisciplinaResult(
                id=str(d.id),
                nombre=d.nombre,
                sigla=d.sigla,
                modalidad=d.modalidad,
                min_jugadores=d.min_jugadores,
                max_jugadores=d.max_jugadores,
            )
        except Disciplina.DoesNotExist:
            return None
