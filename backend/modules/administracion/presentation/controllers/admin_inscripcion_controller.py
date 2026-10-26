"""
AdminInscripcionController — the registrations table and its drilldown
(A3, A4).

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`, evaluated SERVER-SIDE on every request):

- anonymous caller → 401 `AUTHENTICATION_REQUIRED` (JWT runs first),
- authenticated non-admin → 403 `ACTION_NOT_ALLOWED`,
- admin → 200.

Routes:
  GET /administracion/inscripciones       — the registrations table (A3).
  GET /administracion/inscripciones/{id}  — the drilldown (A4).

Both endpoints are READ-ONLY: they never write.
"""
from injector import inject
from ninja import Query
from ninja_extra import api_controller, route

from core.pagination import PaginatedData
from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_inscripcion_presenter import (
    AdminInscripcionPresenter,
)
from modules.administracion.presentation.schemas.admin_inscripcion_schemas import (
    AdminInscripcionDetailOut,
    AdminInscripcionListItemOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireAdmin])
class AdminInscripcionController:
    """Controller of the registrations table and its drilldown."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/inscripciones",
        response={200: ApiResponse[PaginatedData[AdminInscripcionListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_inscripciones(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(
            None, description="Búsqueda sobre responsable y paquete."
        ),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): created_at, estado, responsable, paquete.",
        ),
        estado: str | None = Query(None, description="Estado de la inscripción."),
        paquete_id: str | None = Query(None, description="Paquete (UUID)."),
        promocion_id: str | None = Query(None, description="Promoción (UUID)."),
        responsable_persona_id: str | None = Query(
            None, description="Responsable (UUID de Persona)."
        ),
    ):
        """
        Registrations table of the active event.

        Route: GET /api/administracion/inscripciones

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and answers the canonical paginated shape:
        `data = { items[], total, page, page_size, total_pages }`.

        The active event is resolved SERVER-SIDE; the client never sends
        `evento_id`. Filters combine with AND. An unknown `ordering` or an
        invalid filter value is rejected with 422 `INVALID_REQUEST`.

        Returns:
            ApiResponse[PaginatedData[AdminInscripcionListItemOut]].
        """
        result = await self.orchestrator.listar_inscripciones(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            estado=estado,
            paquete_id=paquete_id,
            promocion_id=promocion_id,
            responsable_persona_id=responsable_persona_id,
        )
        return success_response(AdminInscripcionPresenter.present_listado(result))

    @route.get(
        "/inscripciones/{inscripcion_id}",
        response={200: ApiResponse[AdminInscripcionDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_inscripcion(
        self,
        request,
        inscripcion_id: str,
    ):
        """
        Drilldown of one registration of the active event.

        Route: GET /api/administracion/inscripciones/{inscripcion_id}

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and returns the registration with its teams
        (and their roster), its participants, its purchases, its cup
        assignments, its legal acceptances and its cup balance.

        An unknown id AND an id of another edition are answered the SAME way:
        404 `RESOURCE_NOT_FOUND`. The surface never confirms the existence of
        a resource outside its scope.

        Returns:
            ApiResponse[AdminInscripcionDetailOut].
        """
        result = await self.orchestrator.obtener_inscripcion_detalle(inscripcion_id)
        return success_response(AdminInscripcionPresenter.present_detalle(result))


__all__ = ["AdminInscripcionController"]
