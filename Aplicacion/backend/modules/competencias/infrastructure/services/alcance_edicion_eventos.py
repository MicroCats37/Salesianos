"""El adaptador del ALCANCE de edición.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.10

`modules.eventos` es el DUEÑO del orden congelado de resolución de edición
(`FREEZE-ED-1.0.0` · `FR-02` §2.2). Este adaptador lo CONSUME y lo reproduce
sin duplicarlo: es el mismo patrón que usan `salesianos_fest` y `marketplace`.

El módulo `competencias` lo necesita para las rutas que NO llevan la edición
en el camino — la lista de competencias y la agenda transversal del día.
Todas las demás operaciones cuelgan de una competencia, y su edición es su
alcance (`RN-E01`).
"""

from modules.competencias.domain.ports import IAlcanceEdicion


class AlcanceEdicionEventos(IAlcanceEdicion):
    """Puente con el servicio de alcance de `modules.eventos`."""

    def __init__(self, scope_service=None):
        from modules.eventos.domain.services.core.edicion_scope_service import (
            EdicionScopeService,
        )

        self.scope_service = scope_service or EdicionScopeService()

    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """Nivel 1 del orden congelado. NUNCA hay fallback."""
        return self.scope_service.resolver_explicita(
            edicion_id,
            exigir_publicada=exigir_publicada,
        )

    def resolver_actual(
        self,
        *,
        ediciones_activas_actor=None,
        exigir_publicada: bool = False,
        permitir_publicada_por_defecto: bool = True,
    ):
        """Niveles 2, 3 y 4 del orden congelado."""
        return self.scope_service.resolver_actual(
            ediciones_activas_actor=ediciones_activas_actor,
            exigir_publicada=exigir_publicada,
            permitir_publicada_por_defecto=permitir_publicada_por_defecto,
        )


__all__ = ["AlcanceEdicionEventos"]
