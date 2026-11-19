"""`EdicionController` — superficie HTTP del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/PLAN_REFACTORIZACION.md` §1.A (controladores sagrados) ·
          `contract/django-app-architecture-contract.md` §4.8

Controller DELGADO: parsea la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter. Cero `if`, cero ORM, cero respuestas de
error manuales (los errores los construye el catálogo de `core/exceptions.py`
a partir del código estable de la excepción de dominio).

Rutas (ledger FR-07 §3.3):

| Ruta | Método | Scope | Permiso | Errores |
|---|---|---|---|---|
| `/ediciones/actual` | GET | implícito (resolución) | público | `EDICION_NO_PUBLICADA` 404 · `EDICION_AMBIGUA` 409 · `EDICION_NO_RESUELTA` 404 |

La ruta es PÚBLICA (`auth=None`): es la lectura del catálogo vigente
(`FL-01` paso 1) y no expone datos de ninguna persona.

NOTA DE REGISTRO: una ruta no existe hasta que su controller está registrado
en `config/api.py` (FR-07 §3.1 regla 2). El registro lo hace A0; este paquete
lo deja listo y lo pide explícitamente (evidence FND-02, petición A0-03).
"""

from injector import inject
from ninja_extra import api_controller, route

from core.responses import ApiResponse, success_response
from modules.eventos.domain.services.orchestrators.edicion_orchestrator import (
    EdicionOrchestrator,
)
from modules.eventos.presentation.presenters.edicion_presenter import EdicionPresenter
from modules.eventos.presentation.schemas.edicion_schemas import EdicionActualOut


@api_controller("/ediciones", tags=["Ediciones"], auth=None)
class EdicionController:
    """Superficie HTTP de las ediciones."""

    @inject
    def __init__(self, orchestrator: EdicionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/actual",
        response={200: ApiResponse[EdicionActualOut]},
        summary="Edición vigente y sus módulos habilitados",
    )
    async def edicion_actual(self, request):
        """Edición vigente del sistema.

        Route: GET /api/ediciones/actual

        Devuelve la edición resuelta y el estado de cada módulo lógico. La
        resolución aplica el orden congelado de FR-02 §2.2: nunca elige "la
        primera", "la más reciente" ni "la que coincida con un nombre por
        defecto".
        """
        result = await self.orchestrator.obtener_edicion_actual()
        return success_response(EdicionPresenter.present_actual(result))


__all__ = ["EdicionController"]
