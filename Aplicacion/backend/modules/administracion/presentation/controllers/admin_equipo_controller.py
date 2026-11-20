"""`AdminEquipoController` — la superficie HTTP de los equipos.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

| Ruta | Método | Ledger | Wrapper |
|---|---|---|---|
| `/administracion/equipos` | GET | `RT-IN-09` | `PaginatedData[AdminEquipoListItemOut]` |
| `/administracion/equipos/{equipo_id}` | GET | `RT-IN-10` | `AdminEquipoDetalleOut` |

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
    AdminEquipoDetalleOut,
    AdminEquipoListItemOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminEquipoController:
    """Los equipos del panel de administración."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/equipos",
        response={200: ApiResponse[PaginatedData[AdminEquipoListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="La lista administrativa de los equipos.",
    )
    async def listar_equipos(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None, description="Edición del listado. Sin valor, la edición publicada."
        ),
        q: Optional[str] = Query(None, description="Búsqueda sobre nombre o disciplina."),
        ordering: Optional[str] = Query(
            None, description="Orden (lista blanca): created_at, nombre, disciplina."
        ),
        plantilla: Optional[str] = Query(
            None, description="Filtro de la plantilla: INCOMPLETA o COMPLETA."
        ),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/equipos

        `RT-IN-09`. `plantilla` es el filtro que el resumen declara para
        su drilldown: la lista devuelve exactamente los equipos cuya
        plantilla no llega al mínimo que publica su disciplina.
        """
        items, total, pagina, tamano, paginas = (
            await self.orchestrator.listar_equipos(
                edicion_id=edicion_id,
                q=q or "",
                ordering=ordering or "",
                plantilla=plantilla or "",
                page=page,
                page_size=page_size,
            )
        )

        return paginated_response(
            items=[AdminOperacionPresenter.present_equipo_lista(item) for item in items],
            total=total,
            page=pagina,
            page_size=tamano,
        )

    @route.get(
        "/equipos/{equipo_id}",
        response={200: ApiResponse[AdminEquipoDetalleOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El detalle administrativo de un equipo.",
    )
    async def obtener_equipo(self, request, equipo_id: str):
        """Route: GET /api/administracion/equipos/{equipo_id}

        `RT-IN-10`.
        """
        detalle = await self.orchestrator.obtener_equipo(equipo_id)

        if detalle is None:
            raise NotFoundError(resource="Equipo", code="RESOURCE_NOT_FOUND")

        return success_response(AdminOperacionPresenter.present_equipo_detalle(detalle))


__all__ = ["AdminEquipoController"]
