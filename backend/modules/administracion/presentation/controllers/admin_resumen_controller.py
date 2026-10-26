"""
AdminResumenController — the operational overview and the filter catalogs.

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`, evaluated SERVER-SIDE on every request):

- anonymous caller → 401 `AUTHENTICATION_REQUIRED` (JWT runs first),
- authenticated non-admin → 403 `ACTION_NOT_ALLOWED`,
- admin → 200.

Routes:
  GET /administracion/resumen   — the eight metric blocks (A1).
  GET /administracion/catalogos — the filter option lists (A2).

Both endpoints are READ-ONLY: they never write.
"""
from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_resumen_orchestrator import (
    AdminResumenOrchestrator,
)
from modules.administracion.presentation.presenters.admin_catalogos_presenter import (
    AdminCatalogosPresenter,
)
from modules.administracion.presentation.presenters.admin_resumen_presenter import (
    AdminResumenPresenter,
)
from modules.administracion.presentation.schemas.admin_catalogos_schemas import (
    AdminCatalogosOut,
)
from modules.administracion.presentation.schemas.admin_resumen_schemas import (
    AdminResumenOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireAdmin])
class AdminResumenController:
    """Controller of the operational overview and its filter catalogs."""

    @inject
    def __init__(self, orchestrator: AdminResumenOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/resumen",
        response={200: ApiResponse[AdminResumenOut]},
        auth=JWTAuth(),
    )
    async def resumen(self, request):
        """
        Operational overview of the active event.

        Route: GET /api/administracion/resumen

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and computes EVERY number on the server:
        the eight blocks are the event, the registrations, the payments, the
        cupos, the teams, the participants, the accreditations and the accesses.

        The active event is resolved SERVER-SIDE from
        `settings.EVENTO_ACTIVO_NOMBRE`; the client never sends `evento_id`.
        When there is no active event the endpoint answers 404
        `EVENTO_ACTIVO_NO_ENCONTRADO`.

        Returns:
            ApiResponse[AdminResumenOut] — the eight metric blocks.
        """
        result = await self.orchestrator.obtener_resumen()
        return success_response(AdminResumenPresenter.present_resumen(result))

    @route.get(
        "/catalogos",
        response={200: ApiResponse[AdminCatalogosOut]},
        auth=JWTAuth(),
    )
    async def catalogos(self, request):
        """
        Filter option lists of the active event.

        Route: GET /api/administracion/catalogos

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and reuses the catalog sources of the
        owning modules (disciplines, packages, promotions, categories) plus
        the state vocabularies of the domain — no duplicated business logic.

        Returns:
            ApiResponse[AdminCatalogosOut] — the filter option lists.
        """
        result = await self.orchestrator.obtener_catalogos()
        return success_response(AdminCatalogosPresenter.present_catalogos(result))
