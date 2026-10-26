"""Categoria selector — read-only queries for categorias."""
from typing import List

from ..models import Categoria
from ..results.catalogo_results import CategoriaResult


class CategoriaSelector:
    """Queries for Categoria entities."""

    @staticmethod
    def get_activas() -> List[CategoriaResult]:
        """Return all active categorias."""
        qs = (
            Categoria.objects.filter(esta_activa=True)
            .select_related("evento")
            .order_by("evento__nombre", "nombre")
        )
        return [
            CategoriaResult(
                id=str(c.id),
                evento_id=str(c.evento_id),
                evento_nombre=c.evento.nombre,
                nombre=c.nombre,
                promocion_desde=c.promocion_desde,
                promocion_hasta=c.promocion_hasta,
            )
            for c in qs
        ]

    @staticmethod
    def get_by_evento(evento_id: str) -> List[CategoriaResult]:
        """Return active categorias for a specific evento."""
        qs = (
            Categoria.objects.filter(esta_activa=True, evento_id=evento_id)
            .select_related("evento")
            .order_by("nombre")
        )
        return [
            CategoriaResult(
                id=str(c.id),
                evento_id=str(c.evento_id),
                evento_nombre=c.evento.nombre,
                nombre=c.nombre,
                promocion_desde=c.promocion_desde,
                promocion_hasta=c.promocion_hasta,
            )
            for c in qs
        ]
