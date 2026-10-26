"""
PagosController — Izipay Perú payment endpoints.

Thin async controller — only delegates to PagosOrchestrator.

Routes:
  POST /pagos/izipay/confirmar    - Browser relay of the provider payload
  POST /pagos/izipay/notificacion - Server-to-server provider notification
  GET  /pagos/transacciones/{transaction_id} - Get transaction status
  GET  /pagos/ordenes/{orden_id} - Get order status

SECURITY:
- The browser relay requires an authenticated caller that owns the order.
- The provider notification is public (the provider is not a session) but it
  is accepted ONLY when the merchant signature verifies.
- Reading a transaction or an order requires ownership or administration.
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.pagos.domain.constants import SettlementStatus
from modules.pagos.domain.exceptions import PagoNoAutorizadoError
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator
from modules.pagos.domain.schemas.result import IzipayConfirmResult
from modules.pagos.presentation.schemas.pago_schema import (
    IzipayConfirmIn,
    IzipayConfirmOut,
    IzipayNotificacionIn,
    OrdenPagoOut,
    TransaccionPagoOut,
)
from modules.pagos.presentation.presenters.pago_presenter import IzipayPresenter


# Fixed, user-facing messages. They never interpolate technical values.
_MENSAJE_PAGO_CONFIRMADO = "Pago confirmado correctamente."
_MENSAJE_ACTIVACION_PENDIENTE = (
    "Pago confirmado. La activación comercial está pendiente."
)
_MENSAJE_PAGO_NO_COMPLETADO = "El pago no se completó."


def _mensaje_confirmacion(result: IzipayConfirmResult) -> str:
    """
    Pick the fixed public message for a confirmation result.

    The message reflects the authoritative state: a successful payment whose
    commercial settlement did not complete says so explicitly, so the client
    never reads a paid-but-not-activated order as a finished one.
    """
    if not result.success:
        return _MENSAJE_PAGO_NO_COMPLETADO
    if result.settlement_status == SettlementStatus.SETTLED:
        return _MENSAJE_PAGO_CONFIRMADO
    return _MENSAJE_ACTIVACION_PENDIENTE


def _actor(request) -> tuple[str | None, bool]:
    """
    Resolve who is performing a payment operation.

    Returns (persona_id, es_admin). Administrators act on any order; every
    other caller must be the owner of the order they touch.

    Raises:
        PagoNoAutorizadoError: the caller has no linked persona and no
            administrative authority.
    """
    user = request.user
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return None, True

    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise PagoNoAutorizadoError()

    return str(persona_id), False


@api_controller("/pagos", tags=["Pagos"], permissions=[IsAuthenticated])
class PagosController:
    """
    Controller for Izipay Perú payment operations.

    Every endpoint requires an authenticated caller, except the server-to-server
    provider notification, which is authenticated by the merchant signature.
    Ownership validation happens in the flow, so the browser relay and the
    reads share the same rule.
    """

    @inject
    def __init__(
        self,
        orchestrator: PagosOrchestrator,
    ):
        self.orchestrator = orchestrator

    @route.post(
        "/izipay/confirmar",
        response={200: ApiResponse[IzipayConfirmOut]},
        auth=JWTAuth(),
    )
    async def confirmar_pago(self, request, payload: IzipayConfirmIn):
        """
        Confirm an Izipay Perú payment from the browser relay (kr_answer).

        Route: POST /api/pagos/izipay/confirmar

        The frontend SDK relays the provider payload after the popup closes.
        The caller must be authenticated and must own the order; the payload
        is cross-checked against the persisted transaction. A forged, stale or
        foreign payload changes nothing.

        Idempotent: if the transaction is already confirmed (EXITO), the
        commercial settlement is re-driven (it is idempotent) and the response
        reports already_confirmed=True.

        The purchase linked to the order is settled by the backend — the
        browser never sends a commercial-confirmation request.

        Raises:
            TransaccionPagoNoEncontradaError: unknown transaction.
            PagoNoAutorizadoError: the caller does not own the order.
            PagoDatosInconsistentesError: the payload contradicts the order.
            PagoFirmaInvalidaError: the provider signature does not verify.
        """
        persona_id, es_admin = _actor(request)

        result = await self.orchestrator.confirmar_pago_izipay(
            kr_answer=payload.kr_answer.model_dump(),
            persona_id=persona_id,
            es_admin=es_admin,
        )

        return success_response(
            IzipayPresenter.present_confirm(result),
            message=_mensaje_confirmacion(result),
        )

    @route.post(
        "/izipay/notificacion",
        response={200: ApiResponse[IzipayConfirmOut]},
        auth=None,
        permissions=[AllowAny],
    )
    async def recibir_notificacion(self, payload: IzipayNotificacionIn):
        """
        Receive the server-to-server notification from Izipay Perú.

        Route: POST /api/pagos/izipay/notificacion

        The provider calls this endpoint directly with the raw signed payload.
        It is accepted ONLY when the merchant key is configured and the
        signature verifies — there is no fallback. The confirmation is
        idempotent, so a provider retry converges instead of duplicating.

        Raises:
            PagoNotificacionNoVerificableError: the merchant key is missing.
            PagoFirmaInvalidaError: the signature does not verify.
        """
        result = await self.orchestrator.confirmar_pago_por_notificacion(
            payload_http=payload.payloadHttp,
            signature=payload.signature,
            transaction_id=payload.transactionId,
        )

        return success_response(
            IzipayPresenter.present_confirm(result),
            message=_mensaje_confirmacion(result),
        )

    @route.get(
        "/transacciones/{transaction_id}",
        response={200: ApiResponse[TransaccionPagoOut]},
        auth=JWTAuth(),
    )
    async def obtener_transaccion(self, request, transaction_id: str):
        """
        Get a transaction by its transaction_id.

        Route: GET /api/pagos/transacciones/{transaction_id}

        Restricted to the owner of the order (or an administrator).

        Raises:
            TransaccionPagoNoEncontradaError: transaction not found.
            PagoNoAutorizadoError: the caller does not own the order.
        """
        persona_id, es_admin = _actor(request)

        tx = await self.orchestrator.obtener_transaccion(
            transaction_id=transaction_id,
            persona_id=persona_id,
            es_admin=es_admin,
        )

        return success_response(
            IzipayPresenter.present_transaccion(tx),
            message="Transaccion encontrada.",
        )

    @route.get(
        "/ordenes/{orden_id}",
        response={200: ApiResponse[OrdenPagoOut]},
        auth=JWTAuth(),
    )
    async def obtener_orden(self, request, orden_id: str):
        """
        Get an OrdenPago by its ID.

        Route: GET /api/pagos/ordenes/{orden_id}

        Restricted to the owner of the order (or an administrator).

        Raises:
            OrdenPagoNoEncontradaError: order not found.
            PagoNoAutorizadoError: the caller does not own the order.
        """
        persona_id, es_admin = _actor(request)

        orden = await self.orchestrator.obtener_orden(
            orden_id=orden_id,
            persona_id=persona_id,
            es_admin=es_admin,
        )

        return success_response(
            IzipayPresenter.present_orden_pago(orden),
            message="Orden encontrada.",
        )
