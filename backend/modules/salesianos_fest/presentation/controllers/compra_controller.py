"""
CompraController — Compra commercial purchase endpoints.

Thin async controller — only delegates to CompraOrchestrator.
Authentication required for all operations.

Routes:
  POST /api/compras/                       - Create initial purchase or amplification
  GET  /api/compras/{compra_id}            - Get compra detail
  GET  /api/inscripciones/{id}/compras      - List compras for inscripcion
  POST /api/compras/{compra_id}/iniciar-pago - Generate Izipay token for an order
  POST /api/compras/{compra_id}/cancelar   - Cancel Compra (refund) and revoke its rights

There is NO public settlement route: a purchase is paid by the backend,
right after the payment is verified, or by an administrator through the
manual approval of the administration area (`POST
/api/administracion/pagos/{orden_pago_id}/aprobar-manual`). A buyer can
never confirm their own purchase.
"""
from asgiref.sync import sync_to_async
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from injector import inject
from django.core.exceptions import PermissionDenied

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from core.exceptions import BusinessError, NotFoundError
from modules.salesianos_fest.domain.services.orchestrators.compra_orchestrator import CompraOrchestrator
from modules.salesianos_fest.domain.selectors.compra_selector import CompraSelector
from modules.salesianos_fest.presentation.schemas.compra_schemas import (
    CompraCreateIn,
    CompraCreateOut,
    CompraDetailOut,
    CompraListOut,
    IniciarPagoOut,
    CompraCanceladaOut,
)
from modules.salesianos_fest.presentation.presenters.compra_presenter import CompraPresenter


def _get_authenticated_persona_id(request) -> str:
    """
    Extract persona_id from the authenticated request.
    """
    user = request.user
    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise BusinessError("Usuario sin persona vinculada. Complete su registro.")
    return str(persona_id)


def _validate_compra_ownership(compra, responsable_id: str) -> None:
    """
    Validate that the authenticated user owns this compra.

    A SPORTS purchase is owned by the responsable of its inscription; any
    OTHER purchase (a batch of party passes) is owned by the generic
    `Compra.responsable`. The sports rule is NOT weakened: a purchase with an
    inscription is always checked against that inscription.
    """
    compra_inscripcion = getattr(compra, "compra_inscripcion", None)
    if compra_inscripcion is not None:
        if str(compra_inscripcion.inscripcion.responsable_id) != responsable_id:
            raise PermissionDenied()
        return

    if not compra.responsable_id or str(compra.responsable_id) != responsable_id:
        raise PermissionDenied()


def _is_admin(request) -> bool:
    """Django admin users (is_staff / is_superuser) can act on any compra."""
    user = request.user
    return bool(getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))


@api_controller("/compras", tags=["Compras"], permissions=[IsAuthenticated])
class CompraController:
    """
    Controller for Compra commercial purchase operations.

    All endpoints require JWT authentication.
    Ownership validation ensures users can only operate on their own compras.
    """

    @inject
    def __init__(
        self,
        orchestrator: CompraOrchestrator,
        selector: CompraSelector,
    ):
        self.orchestrator = orchestrator
        self.selector = selector

    @route.post(
        "/",
        response={200: ApiResponse[CompraCreateOut]},
        auth=JWTAuth(),
    )
    async def crear_compra(self, request, payload: CompraCreateIn):
        """
        Create a new Compra (initial purchase or amplification).

        Route: POST /api/compras/

        Creates:
        - OrdenPago in pagos module (PENDIENTE)
        - Compra in salesianos_fest linked to the Inscripcion

        The price is frozen at this moment from the vigentes PaquetePrecio.
        For INICIAL tipo, validates that cantidad >= minimo_compra_inicial.

        Raises:
            BusinessError: if user has no Persona or is not the inscripcion owner.
            NotFoundError: if inscripcion not found.
            ConflictError: if price not found or cantidad insufficient.
        """
        from modules.salesianos_fest.domain.selectors.inscripcion_selector import InscripcionSelector

        responsable_id = _get_authenticated_persona_id(request)

        # Verify inscripcion ownership
        inscripcion_selector = InscripcionSelector()
        inscripcion = await self._sync_call(
            inscripcion_selector.get_by_id, payload.inscripcion_id
        )
        if not inscripcion:
            raise NotFoundError(
                f"Inscripcion {payload.inscripcion_id} no encontrada.",
                code="INSCRIPCION_NOT_FOUND",
            )

        if str(inscripcion.responsable_id) != responsable_id:
            raise PermissionDenied()

        # Create Compra
        from modules.salesianos_fest.domain.schemas.compra_schemas import CompraCreateData
        data = CompraCreateData(
            inscripcion_id=str(payload.inscripcion_id),
            tipo=payload.tipo,
            cantidad=payload.cantidad,
        )
        result = await self.orchestrator.crear_compra(data)

        return success_response(
            CompraPresenter.present_created(result),
            message="Compra creada correctamente. Proceda al pago.",
        )

    @route.get(
        "/{compra_id}",
        response={200: ApiResponse[CompraDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_compra(self, request, compra_id: str):
        """
        Get Compra detail by ID.

        Route: GET /api/compras/{compra_id}

        Raises:
            BusinessError: if user is not the compra's inscripcion owner.
            NotFoundError: if compra not found.
        """
        responsable_id = _get_authenticated_persona_id(request)

        compra = await self._sync_call(self.selector.obtener_por_id, compra_id)
        if not compra:
            raise NotFoundError(
                f"Compra {compra_id} no encontrada.",
                code="COMPRA_NOT_FOUND",
            )

        _validate_compra_ownership(compra, responsable_id)

        return success_response(
            CompraPresenter.present_detail(compra),
            message="Compra encontrada.",
        )

    @route.get(
        "/inscripciones/{inscripcion_id}/compras",
        response={200: ApiResponse[CompraListOut]},
        auth=JWTAuth(),
    )
    async def listar_compras_inscripcion(self, request, inscripcion_id: str):
        """
        List all compras for an inscripcion.

        Route: GET /api/compras/inscripciones/{inscripcion_id}/compras

        Raises:
            BusinessError: if user is not the inscripcion owner.
            NotFoundError: if inscripcion not found.
        """
        from modules.salesianos_fest.domain.selectors.inscripcion_selector import InscripcionSelector

        responsable_id = _get_authenticated_persona_id(request)

        inscripcion_selector = InscripcionSelector()
        inscripcion = await self._sync_call(
            inscripcion_selector.get_by_id, inscripcion_id
        )
        if not inscripcion:
            raise NotFoundError(
                f"Inscripcion {inscripcion_id} no encontrada.",
                code="INSCRIPCION_NOT_FOUND",
            )

        if str(inscripcion.responsable_id) != responsable_id:
            raise PermissionDenied()

        compras = await self._sync_call(
            self.selector.listar_por_inscripcion, inscripcion_id
        )

        return success_response(
            CompraPresenter.present_list(compras),
            message="Compras encontradas.",
        )

    @route.post(
        "/{compra_id}/iniciar-pago",
        response={200: ApiResponse[IniciarPagoOut]},
        auth=JWTAuth(),
    )
    async def iniciar_pago(self, request, compra_id: str):
        """
        Generate Izipay token for a Compra's OrdenPago.

        Route: POST /api/compras/{compra_id}/iniciar-pago

        Validates that the Compra is PENDIENTE and that the user owns it.
        Buyer data is derived from the responsable Persona.

        Raises:
            BusinessError: if user is not the compra's inscripcion owner.
            NotFoundError: if compra not found.
            ConflictError: if compra is not payable.
        """
        responsable_id = _get_authenticated_persona_id(request)

        compra = await self._sync_call(self.selector.obtener_por_id, compra_id)
        if not compra:
            raise NotFoundError(
                f"Compra {compra_id} no encontrada.",
                code="COMPRA_NOT_FOUND",
            )

        _validate_compra_ownership(compra, responsable_id)

        result = await self.orchestrator.iniciar_pago(compra_id)

        return success_response(
            CompraPresenter.present_iniciar_pago(result),
            message="Sesion de pago preparada.",
        )

    @route.post(
        "/{compra_id}/cancelar",
        response={200: ApiResponse[CompraCanceladaOut]},
        auth=JWTAuth(),
    )
    async def cancelar_compra(self, request, compra_id: str):
        """Cancel a Compra (refund) and revoke the rights it funded.

        Only the rights funded by this compra are revoked — assignments paid
        by other compras keep their right. The access of every affected person
        is recalculated.

        Authorization: responsible of the inscripcion OR Django admin.
        """
        responsable_id = None
        if not _is_admin(request):
            responsable_id = _get_authenticated_persona_id(request)

        compra = await self._sync_call(self.selector.obtener_por_id, compra_id)
        if not compra:
            raise NotFoundError(
                f"Compra {compra_id} no encontrada.",
                code="COMPRA_NOT_FOUND",
            )

        if responsable_id is not None:
            _validate_compra_ownership(compra, responsable_id)

        result = await self.orchestrator.cancelar_compra(compra_id)

        return success_response(
            CompraPresenter.present_cancelar(result),
            message="La compra se canceló correctamente.",
        )

    async def _sync_call(self, func, *args, **kwargs):
        """Helper to call a sync function in an async context."""
        return await sync_to_async(func)(*args, **kwargs)
