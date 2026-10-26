"""
AdminFundacionController — the `/administracion` namespace.

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`, evaluated SERVER-SIDE on every request):

- anonymous caller → 401 `AUTHENTICATION_REQUIRED` (JWT runs first),
- authenticated non-admin → 403 `ACTION_NOT_ALLOWED`,
- admin → 200.

Routes:
  GET /administracion/health — foundation probe (Phase 1).
"""
from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_fundacion_orchestrator import (
    AdminFundacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_fundacion_presenter import (
    AdminFundacionPresenter,
)
from modules.administracion.presentation.schemas.admin_fundacion_schemas import (
    AdminHealthOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireAdmin])
class AdminFundacionController:
    """Controller of the operational administration surface."""

    @inject
    def __init__(self, orchestrator: AdminFundacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/health",
        response={200: ApiResponse[AdminHealthOut]},
        auth=JWTAuth(),
    )
    async def health(self, request):
        """
        Probe of the administration module.

        Route: GET /api/administracion/health

        Authorization: Django admin only (is_staff OR is_superuser).
        The endpoint is READ-ONLY: it resolves the active event through the
        `eventos` module selector and returns the state of the module. It
        proves the app registration, the DI wiring and the admin permission
        without exposing any business data.

        Returns:
            ApiResponse[AdminHealthOut] — module, state and active event.
        """
        result = await self.orchestrator.obtener_fundacion()
        return success_response(AdminFundacionPresenter.present_fundacion(result))
