"""Promocion selector — read-only queries for promociones."""
from typing import List

from ..models import Promocion
from ..results.catalogo_results import PromocionResult


class PromocionSelector:
    """Queries for Promocion entities."""

    @staticmethod
    def get_activas() -> List[PromocionResult]:
        """Return all active promociones."""
        qs = Promocion.objects.filter(activa=True).order_by("-anio")
        return [
            PromocionResult(
                id=str(p.id),
                anio=p.anio,
                nombre=p.nombre,
            )
            for p in qs
        ]

    @staticmethod
    def get_by_id(promocion_id: str) -> PromocionResult | None:
        """Return a promocion by ID or None."""
        try:
            p = Promocion.objects.get(id=promocion_id)
            return PromocionResult(
                id=str(p.id),
                anio=p.anio,
                nombre=p.nombre,
            )
        except Promocion.DoesNotExist:
            return None
