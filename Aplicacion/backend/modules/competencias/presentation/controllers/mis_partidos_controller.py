"""`MisPartidosController` — los partidos de la cuenta.

Change: `partidos-marcadores-competencias` · Batch 3B

| Ruta | Método | Wrapper |
|---|---|---|
| `GET /api/cuenta/mis-partidos` | GET | `MisPartidosOut` |

El prefijo `/cuenta` es el de las lecturas de la CUENTA (`GET
/api/cuenta/compras`): es DISJUNTO de `/api/competencias/**` —que exige
capacidad administrativa— y de `/api/publico/**` —que es anónimo—.

La ruta exige una SESIÓN (`JWTAuth`) pero NO una capacidad: es la lectura de
un usuario normal sobre SUS propios partidos.

**La identidad la decide el servidor.** La ruta no acepta ninguna persona,
usuario ni equipo: el `persona_fk_id` de la sesión es la única entrada. Una
cuenta sin `Persona`, sin participaciones o sin equipos recibe una lista
VACÍA: nunca un error y nunca los partidos de otra cuenta.
"""

from injector import inject
from ninja_extra import api_controller, route

from core.responses import ApiResponse, success_response
from modules.competencias.domain.services.orchestrators.competencias_orchestrator import (
    CompetenciasOrchestrator,
)
from modules.competencias.presentation.presenters.mis_partidos_presenter import (
    MisPartidosPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    MisPartidosOut,
)
from ninja_jwt.authentication import JWTAuth


@api_controller("/cuenta", tags=["Cuenta"])
class MisPartidosController:
    """Los partidos de la cuenta que está conectada."""

    @inject
    def __init__(self, orchestrator: CompetenciasOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/mis-partidos",
        response={200: ApiResponse[MisPartidosOut]},
        auth=JWTAuth(),
        summary="Los partidos de la cuenta",
    )
    async def listar_mis_partidos(self, request):
        """Route: GET /api/cuenta/mis-partidos

        La identidad sale de la sesión (`request.user.persona_fk_id`). El
        cliente no envía ningún identificador de persona, usuario o equipo.
        """
        persona_id = getattr(request.user, "persona_fk_id", None)
        resultado = await self.orchestrator.obtener_mis_partidos(
            str(persona_id) if persona_id is not None else None
        )
        return success_response(MisPartidosPresenter.present(resultado))


__all__ = ["MisPartidosController"]
