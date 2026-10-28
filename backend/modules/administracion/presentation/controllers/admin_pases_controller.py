"""
AdminPasesController — the administrative cancellation of a pass purchase.

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the route is gated by `RequirePagosAprobar` (the capability
`admin.pagos.aprobar`), held ONLY by the break-glass tier: cancelling a
purchase and revoking the rights it funded is a SENSITIVE decision and the
operational staff does NOT take it.

Every gate is evaluated SERVER-SIDE on every request: anonymous → 401,
authenticated non-admin → 403, operational staff → 403, break-glass → 200.

Routes:
  POST /administracion/pases/compras/{compra_id}/cancelar — cancel a pass
       purchase, revoking the nominative rights it funded.

This operation is NOT a monetary refund: it cancels the purchase and its
order and revokes the rights that were delivered with them.
"""

from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequirePagosAprobar, RequirePagosVer
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_pases_presenter import (
    AdminPasesPresenter,
)
from modules.administracion.presentation.schemas.admin_pases_schemas import (
    AdminPaseCanceladaOut,
    AdminPaseCancelarIn,
)


@api_controller("/administracion/pases", tags=["Administración"], permissions=[RequirePagosVer])
class AdminPasesController:
    """Controller of the administrative pass operations."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.post(
        "/compras/{compra_id}/cancelar",
        response={200: ApiResponse[AdminPaseCanceladaOut]},
        auth=JWTAuth(),
        permissions=[RequirePagosAprobar],
    )
    async def cancelar_compra_pase(
        self,
        request,
        compra_id: str,
        payload: AdminPaseCancelarIn,
    ):
        """
        Cancel a pass purchase (administrative).

        Route: POST /api/administracion/pases/compras/{compra_id}/cancelar

        Authorization: the capability `admin.pagos.aprobar` — the break-glass
        tier only. The operational staff gets 403.

        The purchase and its payment order are cancelled, the nominative
        rights it funded are revoked (permanently) and the effective access of
        every affected person is recomputed. The motive is mandatory and the
        decision is audited.

        It is NOT a monetary refund.

        Raises:
            NotFoundError: the purchase is not a pass purchase.
        """
        result = await self.orchestrator.cancelar_compra_pase(
            compra_id,
            str(request.auth.id),
            payload.motivo,
        )
        return success_response(
            AdminPasesPresenter.present_cancelar_compra_pase(result),
            message="La compra de pases fue cancelada correctamente.",
        )


__all__ = ["AdminPasesController"]
