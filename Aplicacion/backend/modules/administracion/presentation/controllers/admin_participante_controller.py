"""`AdminParticipanteController` — la superficie HTTP de los participantes.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

| Ruta | Método | Ledger | Wrapper |
|---|---|---|---|
| `/administracion/participantes` | GET | `RT-IN-11` | `PaginatedData[ParticipanteAdminOut]` |

**401 ANTES QUE 403**: `auth=JWTAuth()` + la capacidad `admin.ver`.
"""

from typing import Optional

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.pagination import PaginatedData
from core.permissions import RequireAdminVer
from core.responses import ApiResponse, paginated_response
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_operacion_presenter import (
    AdminOperacionPresenter,
)
from modules.administracion.presentation.schemas.admin_operacion_schemas import (
    ParticipanteAdminOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminParticipanteController:
    """Los participantes del panel de administración."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/participantes",
        response={200: ApiResponse[PaginatedData[ParticipanteAdminOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="La lista administrativa de los participantes.",
    )
    async def listar_participantes(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None, description="Edición del listado. Sin valor, la edición publicada."
        ),
        q: Optional[str] = Query(None, description="Búsqueda sobre nombre o documento."),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/participantes

        `RT-IN-11`. La lista es de PERSONAS con sus participaciones: el
        conflicto de una participación (la misma persona activa dos veces
        en la misma disciplina) lo declara el backend, nunca el navegador.
        """
        items, total, pagina, tamano, paginas = (
            await self.orchestrator.listar_participantes(
                edicion_id=edicion_id,
                q=q or "",
                page=page,
                page_size=page_size,
            )
        )

        return paginated_response(
            items=[AdminOperacionPresenter.present_participante_admin(item) for item in items],
            total=total,
            page=pagina,
            page_size=tamano,
        )


__all__ = ["AdminParticipanteController"]
