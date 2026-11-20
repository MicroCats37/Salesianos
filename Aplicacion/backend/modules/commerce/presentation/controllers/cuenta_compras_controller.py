"""Account-scoped commercial purchase history."""

from injector import inject
from ninja_extra import api_controller, route

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.commerce.domain.services.orchestrators.compra_orchestrator import (
    CompraOrchestrator,
)
from modules.commerce.presentation.presenters.cuenta_compras_presenter import (
    CuentaComprasPresenter,
)
from modules.commerce.presentation.schemas.cuenta_compras_schemas import CompraCuentaOut


@api_controller("/cuenta", tags=["Cuenta"])
class CuentaComprasController:
    """Read-only account history over the shared commercial aggregate."""

    @inject
    def __init__(self, orchestrator: CompraOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/compras",
        response={200: ApiResponse[list[CompraCuentaOut]]},
        auth=JWTAuth(),
        summary="Historial comercial de la cuenta",
    )
    async def listar_compras(self, request):
        """Route: GET /api/cuenta/compras."""
        persona_id = getattr(request.user, "persona_fk_id", None)
        if persona_id is None:
            return success_response([])

        resultados = await self.orchestrator.listar_por_persona(str(persona_id))
        return success_response(CuentaComprasPresenter.present_listado(resultados))


__all__ = ["CuentaComprasController"]
