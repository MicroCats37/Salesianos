"""`AdminPersonaController` — la superficie HTTP de las personas.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

| Ruta | Método | Ledger | Wrapper |
|---|---|---|---|
| `/administracion/personas` | GET | `RT-ID-07` | `PaginatedData[AdminPersonaListItemOut]` |
| `/administracion/personas/{persona_id}` | GET | `RT-ID-08` | `AdminPersonaDetalleOut` |

**401 ANTES QUE 403**: `auth=JWTAuth()` + la capacidad `admin.ver`.
"""

from typing import Optional

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.exceptions import NotFoundError
from core.pagination import PaginatedData
from core.permissions import RequireAdminVer
from core.responses import ApiResponse, paginated_response, success_response
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_operacion_presenter import (
    AdminOperacionPresenter,
)
from modules.administracion.presentation.schemas.admin_operacion_schemas import (
    AdminPersonaDetalleOut,
    AdminPersonaListItemOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminPersonaController:
    """Las personas del panel de administración."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/personas",
        response={200: ApiResponse[PaginatedData[AdminPersonaListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="La búsqueda administrativa de personas.",
    )
    async def listar_personas(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None,
            description=(
                "Acota las participaciones que se publican. El conjunto de "
                "personas no se acota: la búsqueda es global."
            ),
        ),
        q: Optional[str] = Query(None, description="Búsqueda sobre nombre o documento."),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/personas

        `RT-ID-07`. La búsqueda es GLOBAL: no hay edición que resolver y
        por tanto no hay ambigüedad posible.
        """
        items, total, pagina, tamano, paginas = (
            await self.orchestrator.listar_personas(
                q=q or "",
                edicion_id=edicion_id,
                page=page,
                page_size=page_size,
            )
        )

        return paginated_response(
            items=[AdminOperacionPresenter.present_persona_lista(item) for item in items],
            total=total,
            page=pagina,
            page_size=tamano,
        )

    @route.get(
        "/personas/{persona_id}",
        response={200: ApiResponse[AdminPersonaDetalleOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El detalle administrativo de una persona.",
    )
    async def obtener_persona(
        self,
        request,
        persona_id: str,
        edicion_id: Optional[str] = Query(
            None, description="Acota las participaciones que se publican."
        ),
    ):
        """Route: GET /api/administracion/personas/{persona_id}

        `RT-ID-08`.
        """
        detalle = await self.orchestrator.obtener_persona(persona_id, edicion_id=edicion_id)

        if detalle is None:
            raise NotFoundError(resource="Persona", code="RESOURCE_NOT_FOUND")

        return success_response(AdminOperacionPresenter.present_persona_detalle(detalle))


__all__ = ["AdminPersonaController"]
