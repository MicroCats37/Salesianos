"""Selectores de patrocinadores y de su galería.

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

REGLA (F-26): un selector que devuelve un `QuerySet` es una mina en un
contexto async: la consulta es perezosa y recorrerla dentro de una función
async lanza `SynchronousOnlyOperation`. Por eso TODOS los selectores de este
módulo devuelven LISTAS ya evaluadas.

Las consultas son de lectura y no modifican el alcance: el filtro por edición
es siempre explícito (`edicion_id`), nunca implícito.
"""

from modules.patrocinadores.domain.models import Patrocinador, PatrocinadorImagen


class PatrocinadorSelector:
    """Consultas de lectura sobre `Patrocinador` y su galería."""

    def listar_por_edicion(
        self, edicion_id, visible: bool | None = None
    ) -> list[Patrocinador]:
        """Patrocinadores de una edición, evaluados en lista.

        El orden es el canónico del modelo (`nombre`, `id`). `visible` filtra
        el consumo público: `True` sólo los visibles, `False` sólo los
        ocultos, `None` todos.
        """
        consulta = Patrocinador.objects.filter(edicion_id=edicion_id)
        if visible is not None:
            consulta = consulta.filter(visible=visible)
        return list(consulta.select_related("edicion"))

    def obtener_por_id(self, patrocinador_id) -> Patrocinador | None:
        """Un patrocinador por identificador, o `None`."""
        return (
            Patrocinador.objects.filter(id=patrocinador_id)
            .select_related("edicion")
            .first()
        )

    def obtener_por_slug(self, edicion_id, slug: str) -> Patrocinador | None:
        """Un patrocinador por slug DENTRO de una edición, o `None`."""
        return (
            Patrocinador.objects.filter(edicion_id=edicion_id, slug=slug)
            .select_related("edicion")
            .first()
        )

    def listar_imagenes(self, patrocinador_id) -> list[PatrocinadorImagen]:
        """La galería de un patrocinador en el orden canónico (`orden`, `id`)."""
        return list(PatrocinadorImagen.objects.filter(patrocinador_id=patrocinador_id))

    def contar_por_edicion(self, edicion_id, visible: bool | None = None) -> int:
        """Cuántos patrocinadores hay en una edición."""
        consulta = Patrocinador.objects.filter(edicion_id=edicion_id)
        if visible is not None:
            consulta = consulta.filter(visible=visible)
        return consulta.count()


__all__ = ["PatrocinadorSelector"]
