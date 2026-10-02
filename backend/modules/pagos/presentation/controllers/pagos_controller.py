"""
PagosController — Izipay Perú payment endpoints.

Thin async controller — only delegates to PagosOrchestrator.
Authentication required; ownership validated server-side.

Routes:
  GET  /api/pagos/izipay/preparar/{inscripcion_id}
  POST /api/pagos/izipay/confirmar
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from core.exceptions import BusinessError, NotFoundError
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator
from modules.pagos.presentation.schemas.pago_schema import (
    IzipayPrepareOut,
    IzipayConfirmIn,
    IzipayConfirmOut,
)
from modules.pagos.presentation.presenters.pago_presenter import IzipayPresenter


def _get_authenticated_persona_id(request) -> str:
    """
    Extract persona_id from the authenticated request.

    The request must have a valid JWT with an authenticated Usuario.
    Uses request.user.persona_fk_id (Usuario -> Persona FK).

    Raises BusinessError if user has no Persona linked.
    """
    user = request.user
    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise BusinessError("Usuario sin persona vinculada. Complete su registro.")
    return str(persona_id)


@api_controller("/pagos", tags=["Pagos"], permissions=[AllowAny])
class PagosController:
    """
    Controller for Izipay Perú payment operations.

    All endpoints require JWT authentication.
    Buyer data for prepare is derived server-side from the authenticated Persona.

    Rutas:
      GET  /pagos/izipay/preparar/{inscripcion_id} -> preparar_pago
      POST /pagos/izipay/confirmar                 -> confirmar_pago
    """

    @inject
    def __init__(self, orchestrator: PagosOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/izipay/preparar/{inscripcion_id}",
        response={200: ApiResponse[IzipayPrepareOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def preparar_pago(self, request, inscripcion_id: str):
        """
        Prepare an Izipay Perú payment session for an inscription.

        Route: GET /api/pagos/izipay/preparar/{inscripcion_id}
        No request body. All buyer/amount/order data is derived server-side.

        The inscription ownership is validated server-side: only the responsible
        person (authenticated via JWT) can prepare a payment for their inscription.

        Buyer data (email, name, surname, document, phone) is derived from
        the authenticated user's Persona record via the InscripcionSelector.
        The client CANNOT choose identity, amount, order, or merchant data.

        Raises:
            BusinessError: if user has no Persona or is not the inscription owner.
            NotFoundError: if inscription not found.
            IzipayError: if inscription is not payable or provider call fails.
        """
        from asgiref.sync import sync_to_async
        from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector

        responsable_id = _get_authenticated_persona_id(request)

        # Verify inscription ownership via selector (includes select_related responsable)
        selector = InscripcionSelector()
        inscripcion = await sync_to_async(selector.obtener_inscripcion)(inscripcion_id)

        if not inscripcion:
            raise NotFoundError(
                f"Inscripción {inscripcion_id} no encontrada.",
                code="INSCRIPCION_NOT_FOUND",
            )

        if str(inscripcion.responsable_id) != responsable_id:
            raise BusinessError(
                "No tienes permiso para preparar el pago de esta inscripción."
            )

        # Buyer data is derived server-side from inscripcion.responsable (Persona).
        # The orchestrator forwards to flujo which derives buyer fields from the
        # Persona record linked to the inscription's responsable.
        result = await self.orchestrator.preparar_pago_izipay(
            inscripcion_id=inscripcion_id,
        )

        return success_response(
            IzipayPresenter.present_prepare(result),
            message="Sesión de pago preparada correctamente.",
        )

    @route.post(
        "/izipay/confirmar",
        response={200: ApiResponse[IzipayConfirmOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def confirmar_pago(self, request, payload: IzipayConfirmIn):
        """
        Confirm an Izipay Perú payment from the frontend callback (kr_answer).

        The frontend SDK sends kr_answer directly to this endpoint after the
        popup closes. This is NOT a server-to-server retrieval.

        Before processing, validates that the transaction belongs to an inscription
        owned by the authenticated user (prevents one user from confirming another's
        transaction).

        Idempotent: if the transaction is already confirmed (EXITO), returns
        immediately with already_confirmed=True.

        Raises:
            BusinessError: if user has no Persona or transaction doesn't belong
                           to their inscription.
            IzipayError: if transaction not found or validation fails.
        """
        responsable_id = _get_authenticated_persona_id(request)

        result = await self.orchestrator.confirmar_pago_izipay(
            kr_answer=payload.kr_answer,
            authenticated_persona_id=responsable_id,
        )

        return success_response(
            IzipayPresenter.present_confirm(result),
            message="Pago confirmado correctamente.",
        )
