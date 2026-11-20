"""`AdminResumenOrchestrator` — la fachada async del resumen operativo.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El orquestador NO decide el alcance: usa el ORDEN CONGELADO de resolución de
edición (`FREEZE-ED-1.0.0` · `FR-02` §2.2) a través del servicio del módulo
`eventos`. No hay un fallback silencioso: si la edición no se puede resolver,
la respuesta es el error del catálogo.

Es una LECTURA, así que el nivel 3 (edición PUBLICADA única) está permitido: la
consulta no muta nada. Con `edicion_id` explícito el nivel 1 no hace fallback
de ningún tipo.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.administracion.domain.results.admin_resultados import (
    ResumenOperativoResultado,
)
from modules.administracion.domain.selectors.admin_resumen_selector import (
    AdminResumenSelector,
)
from modules.eventos.domain.services.core.edicion_scope_service import (
    EdicionScopeService,
)


class AdminResumenOrchestrator:
    """Fachada async del resumen operativo de una edición."""

    @inject
    def __init__(
        self,
        selector: AdminResumenSelector,
        scope: EdicionScopeService,
    ):
        self.selector = selector
        self.scope = scope

    async def obtener_resumen(self, edicion_id=None) -> ResumenOperativoResultado:
        """El resumen de la edición resuelta.

        `edicion_id` explícito: nivel 1 del orden congelado, sin fallback.
        Sin `edicion_id`: niveles 2 y 3, con el mismo orden y los mismos
        errores (409 ante ambigüedad, 404 cuando no hay edición publicada).
        """
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)

        metricas = await sync_to_async(self.selector.metricas)(edicion.id)
        incidencias = await sync_to_async(self.selector.incidencias)(edicion.id)

        return ResumenOperativoResultado(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            edicion_estado=edicion.estado,
            metricas=metricas,
            incidencias=incidencias,
        )

    def _resolver_edicion(self, edicion_id):
        """La edición del alcance, con el orden congelado de `FR-02`."""
        if edicion_id:
            return self.scope.resolver_explicita(edicion_id)

        return self.scope.resolver_actual(permitir_publicada_por_defecto=True)


__all__ = ["AdminResumenOrchestrator"]
