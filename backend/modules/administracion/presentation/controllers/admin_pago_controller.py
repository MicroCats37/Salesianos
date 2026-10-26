"""
AdminPagoController — the payments table and its drilldown (A5, A6).

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`, evaluated SERVER-SIDE on every request):
anonymous → 401, authenticated non-admin → 403, admin → 200.

Routes:
  GET /administracion/pagos              — the payments table (A5).
  GET /administracion/pagos/{orden_pago_id} — the drilldown (A6).

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
from modules.administracion.presentation.presenters.admin_pago_presenter import (
    AdminPagoPresenter,
)
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminPagoDetailOut,
    AdminPagoListItemOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireAdmin])
class AdminPagoController:
    """Controller of the payments table and its drilldown."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/pagos",
        response={200: ApiResponse[PaginatedData[AdminPagoListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_pagos(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(
            None, description="Búsqueda sobre número de orden y responsable."
        ),
        ordering: str | None = Query(
            None,
            description=(
                "Orden (lista blanca): created_at, total, cantidad, "
                "estado_compra, estado_orden, pagada_en."
            ),
        ),
        estado_compra: str | None = Query(
            None, description="Estado comercial de la compra."
        ),
        estado_orden: str | None = Query(None, description="Estado de la orden."),
        tipo: str | None = Query(None, description="INICIAL o AMPLIACION."),
        desde: str | None = Query(None, description="Fecha inicial (ISO)."),
        hasta: str | None = Query(None, description="Fecha final (ISO)."),
    ):
        """
        Payments table of the active event.

        Route: GET /api/administracion/pagos

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and answers the canonical paginated shape.
        The amounts come from the FROZEN commercial snapshot of the purchase.

        The response NEVER carries `metadata`, `token_sesion`,
        `response_message` nor `transaction_id`: the wrapper declares only the
        explicit, safe fields.

        Returns:
            ApiResponse[PaginatedData[AdminPagoListItemOut]].
        """
        result = await self.orchestrator.listar_pagos(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            estado_compra=estado_compra,
            estado_orden=estado_orden,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
        )
        return success_response(AdminPagoPresenter.present_listado(result))

    @route.get(
        "/pagos/{orden_pago_id}",
        response={200: ApiResponse[AdminPagoDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_pago(
        self,
        request,
        orden_pago_id: str,
    ):
        """
        Drilldown of one payment order of the active event.

        Route: GET /api/administracion/pagos/{orden_pago_id}

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and returns the order with its payment
        attempts. The attempts carry EXPLICIT fields only: no `metadata`, no
        `token_sesion`, no `response_message`, no `transaction_id`.

        An unknown order AND an order of another edition are answered the SAME
        way: 404 `RESOURCE_NOT_FOUND`.

        Returns:
            ApiResponse[AdminPagoDetailOut].
        """
        result = await self.orchestrator.obtener_pago_detalle(orden_pago_id)
        return success_response(AdminPagoPresenter.present_detalle(result))


__all__ = ["AdminPagoController"]
