"""Adaptador del alcance de edición para el módulo `patrocinadores`.

Freeze: `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.10 (ports)

Este adaptador es la IMPLEMENTACIÓN del puerto `IAlcanceEdicion` declarado por
el propio dominio `patrocinadores`. Aísla la dependencia con el módulo
`eventos`, que es el dueño del ORDEN ÚNICO de resolución (FR-02 §2.2):

    | # | Origen                       | Regla
    | 1 | `edicion_id` explícito      | sin fallback
    | 2 | Edición activa del actor     | la provee el actor
    | 3 | Edición PUBLICADA única     | la usa el catálogo y la escritura
    | 4 | Sin resolución               | error explícito

Por qué el nivel 3 se aplica también a las ESCRITURAS administrativas: la
edición publicada es ÚNICA por evento (lo impone una `UniqueConstraint`
condicional en la base de datos), es la MISMA edición que la interfaz de
administración muestra (`GET /ediciones/actual`) y la ambigüedad es imposible
por construcción. Ante la ausencia o la ambigüedad, la respuesta es un error
del catálogo: nunca se opera sobre "la edición que haya".
"""

from modules.patrocinadores.domain.ports.alcance_edicion import IAlcanceEdicion


class AlcanceEdicionEventos(IAlcanceEdicion):
    """Implementación de `IAlcanceEdicion` sobre el módulo `eventos`."""

    def __init__(self, scope_service=None):
        if scope_service is None:
            from modules.eventos.domain.services.core.edicion_scope_service import (
                EdicionScopeService,
            )

            scope_service = EdicionScopeService()
        self.scope_service = scope_service

    def resolver_actual(self):
        """La edición vigente según el orden congelado de FR-02 §2.2."""
        return self.scope_service.resolver_actual(permitir_publicada_por_defecto=True)

    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """La edición indicada por identificador, sin fallback alguno."""
        return self.scope_service.resolver_explicita(
            edicion_id, exigir_publicada=exigir_publicada
        )


__all__ = ["AlcanceEdicionEventos"]
