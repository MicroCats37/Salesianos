"""
AdminPagoController — the payments table and its drilldown (A5, A6) and the
administrative approval / annulment of a manual payment.

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the READ routes are gated by `RequirePagosVer` (the capability
`admin.pagos.ver`, held by the operational staff and by the break-glass tier).

The two WRITE routes are gated by `RequirePagosAprobar` (the capability
`admin.pagos.aprobar`), held ONLY by the break-glass tier: approving or
annulling a payment is a sensitive decision and the operational staff does
NOT take it. A route-level permission list REPLACES the one of the
controller, so the sensitive route declares its own gate.

Every gate is evaluated SERVER-SIDE on every request: anonymous → 401,
authenticated non-admin → 403, admin → 200 (or 403 for the staff on the
sensitive writes).

Routes:
  GET  /administracion/pagos              — the payments table (A5).
  GET  /administracion/pagos/{orden_pago_id} — the drilldown (A6).
  POST /administracion/pagos/{orden_pago_id}/aprobar-manual — approve a
       payment received outside the provider.
  POST /administracion/pagos/{orden_pago_id}/anular-manual  — annul that
       approval, revoking the rights it funded.

The two WRITE endpoints NEVER create a provider transaction: a manual
payment did not go through the provider, and fabricating a transaction would
corrupt the reconciliation and the audit trail.
"""
from injector import inject
from ninja import Query
from ninja_extra import api_controller, route

from core.pagination import PaginatedData
from core.permissions import RequirePagosAprobar, RequirePagosVer
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_pago_presenter import (
    AdminPagoPresenter,
)
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminPagoAnularManualIn,
    AdminPagoAnularManualOut,
    AdminPagoAprobarManualIn,
    AdminPagoAprobarManualOut,
    AdminPagoDetailOut,
    AdminPagoListItemOut,
)
from modules.pagos.domain.schemas.aprobacion_pago_manual_schemas import (
    AprobacionPagoManualData,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequirePagosVer])
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

        Authorization: the capability `admin.pagos.ver` (operational staff and
        break-glass tier).

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

        Authorization: the capability `admin.pagos.ver` (operational staff and
        break-glass tier).

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

    @route.post(
        "/pagos/{orden_pago_id}/aprobar-manual",
        response={200: ApiResponse[AdminPagoAprobarManualOut]},
        auth=JWTAuth(),
        permissions=[RequirePagosAprobar],
    )
    async def aprobar_pago_manual(
        self,
        request,
        orden_pago_id: str,
        payload: AdminPagoAprobarManualIn,
    ):
        """
        Approve a payment received outside the payment provider.

        Route: POST /api/administracion/pagos/{orden_pago_id}/aprobar-manual

        Authorization: the capability `admin.pagos.aprobar` — the break-glass
        tier only. The operational staff gets 403.

        The evidence is registered BEFORE the commercial settlement, so a
        settlement failure leaves the proof of the payment durable and the
        activation pending. The amount and the currency must match the order
        EXACTLY and the operation is idempotent: approving twice never
        duplicates the approval nor the rights.

        The endpoint NEVER creates a provider transaction.

        Returns:
            ApiResponse[AdminPagoAprobarManualOut].
        """
        data = AprobacionPagoManualData(
            canal=payload.canal,
            referencia=payload.referencia,
            monto=payload.monto,
            moneda=payload.moneda,
            motivo=payload.motivo,
        )
        result = await self.orchestrator.aprobar_pago_manual(
            orden_pago_id,
            data,
            str(request.auth.id),
        )
        return success_response(
            AdminPagoPresenter.present_aprobar_manual(result),
            message="El pago manual se registró correctamente.",
        )

    @route.post(
        "/pagos/{orden_pago_id}/anular-manual",
        response={200: ApiResponse[AdminPagoAnularManualOut]},
        auth=JWTAuth(),
        permissions=[RequirePagosAprobar],
    )
    async def anular_pago_manual(
        self,
        request,
        orden_pago_id: str,
        payload: AdminPagoAnularManualIn,
    ):
        """
        Annul the manual approval of a payment order.

        Route: POST /api/administracion/pagos/{orden_pago_id}/anular-manual

        Authorization: the capability `admin.pagos.aprobar` — the break-glass
        tier only. The operational staff gets 403.

        The approval, the order and the purchase are updated atomically with
        the actor, the date and the motive, and ONLY the rights funded by
        that purchase are revoked. The operation is idempotent: annulling
        twice never revokes anything twice.

        This is NOT a monetary refund.

        Returns:
            ApiResponse[AdminPagoAnularManualOut].
        """
        result = await self.orchestrator.anular_pago_manual(
            orden_pago_id,
            str(request.auth.id),
            payload.motivo,
        )
        return success_response(
            AdminPagoPresenter.present_anular_manual(result),
            message="La aprobación manual del pago se anuló correctamente.",
        )


__all__ = ["AdminPagoController"]
