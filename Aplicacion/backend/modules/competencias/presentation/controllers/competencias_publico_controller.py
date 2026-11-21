"""`CompetenciasPublicoController` — la superficie PÚBLICA de los encuentros.

Change: `partidos-marcadores-competencias` · Batch 1

| Ruta | Método | Wrapper |
|---|---|---|
| `GET /api/publico/competencias/encuentros` | GET | `EncuentrosPublicosOut` |

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al orquestador
y devuelve el éxito formateado por el presenter. Los errores los traduce el
catálogo global de `core/exceptions.py`; este archivo no construye respuestas
de error.

**La ruta es ANÓNIMA**: `auth=None` + `permissions=[AllowAny]`. El espectador
no tiene sesión: el estado de un encuentro publicado no es un dato reservado.

**La superficie es de SOLO LECTURA.** Publicar un encuentro no es escribirlo:
esta ruta no registra ningún comando, no audita y no muta nada.

**El prefijo NO cuelga de `/api/competencias/`**: esa superficie exige
capacidad administrativa (`SUPERFICIES_CON_CAPACIDAD`, en la frontera de
permisos) y una lectura pública no puede vivir debajo de ella.
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.competencias.domain.services.orchestrators.competencias_orchestrator import (
    CompetenciasOrchestrator,
)
from modules.competencias.presentation.presenters.competencias_publico_presenter import (
    CompetenciasPublicoPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    EncuentrosPublicosOut,
)


@api_controller("/publico/competencias", tags=["Competencias públicas"])
class CompetenciasPublicoController:
    """La lectura pública de los encuentros de la edición publicada."""

    @inject
    def __init__(self, orchestrator: CompetenciasOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/encuentros",
        response={200: ApiResponse[EncuentrosPublicosOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Los encuentros publicables de la edición, en sus tres cubos.",
    )
    async def listar_encuentros(self, request):
        """Route: GET /api/publico/competencias/encuentros

        Lo que está EN JUEGO, lo que VIENE y lo que YA TERMINÓ. La edición la
        resuelve el servidor: el navegador no la elige. Si el comité todavía
        no publicó encuentros, la respuesta es una lista VACÍA —no un error—
        porque no hay nada que mostrar todavía.
        """
        resultado = await self.orchestrator.obtener_encuentros_publicos()
        return success_response(CompetenciasPublicoPresenter.present_encuentros(resultado))


__all__ = ["CompetenciasPublicoController"]
