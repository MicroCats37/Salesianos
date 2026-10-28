"""
PaseController — public catalogue and purchase of independent party passes.

Thin async controller — only delegates to PaseOrchestrator.
No ORM, no business logic, no manual error responses.

Routes:
  GET  /api/pases/                    - Public catalogue of the active passes
  POST /api/pases/comprar              - Buy a batch of passes (authenticated)
  GET  /api/pases/compras/{compra_id}  - State of a pass purchase (owner only)
"""
from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.salesianos_fest.domain.services.orchestrators.pase_orchestrator import (
    PaseOrchestrator,
)
from modules.salesianos_fest.presentation.presenters.pase_presenter import PasePresenter
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    PaseComprarIn,
    PaseListOut,
    PaseCompraCreadaOut,
    PaseCompraEstadoOut,
    PaseBeneficiariosAsignarIn,
    PaseBeneficiarioRevocarIn,
    PaseBeneficiariosListaOut,
    PaseBeneficiariosAsignadosOut,
    PaseBeneficiarioRevocadoOut,
)


@api_controller("/pases", tags=["Pases de fiesta"], permissions=[AllowAny])
class PaseController:
    """
    Catalogue and purchase of the independent party passes.

    The catalogue is public (like the sports catalogue); the purchase and the
    purchase detail require an authenticated buyer.
    """

    @inject
    def __init__(self, orchestrator: PaseOrchestrator):
        self.orchestrator = orchestrator

    @route.get("/", response={200: ApiResponse[list[PaseListOut]]}, auth=None)
    async def listar_pases(self):
        """
        List the passes that can be purchased right now.

        Route: GET /api/pases/
        Auth: público.
        Returns: the ACTIVE passes of the ACTIVE event. The list is empty
                 while the rollout flag is off or when there is no active
                 pass — an unpublished catalogue is never leaked.
        """
        resultados = await self.orchestrator.listar_catalogo()
        pases = PasePresenter.present_pases(resultados)
        return success_response(pases, message="Pases listados correctamente.")

    @route.post(
        "/comprar",
        response={200: ApiResponse[PaseCompraCreadaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def comprar_pases(self, request, payload: PaseComprarIn):
        """
        Buy a batch of passes.

        Route: POST /api/pases/comprar

        Creates atomically a purchase (PENDIENTE), its payment order
        (PENDIENTE) and the commercial line of the batch. The price is frozen
        from the currently vigente pass price: the client never controls the
        price nor the total. No sports object is created.

        Raises:
            BusinessError: the user has no Persona.
            ConflictError: the capability is off, the pass is not available,
                there is no vigente price or the inventory is exhausted.
            UnprocessableEntityError: the quantity is invalid.
        """
        responsable_id = getattr(request.user, "persona_fk_id", None)

        result = await self.orchestrator.comprar_pases(
            responsable_id=responsable_id,
            pase_id=payload.pase_id,
            cantidad=payload.cantidad,
        )

        return success_response(
            PasePresenter.present_compra_creada(result),
            message="Compra de pases registrada correctamente. Proceda al pago.",
        )

    @route.get(
        "/compras/{compra_id}",
        response={200: ApiResponse[PaseCompraEstadoOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def obtener_compra_pase(self, request, compra_id: str):
        """
        Get the state of a pass purchase.

        Route: GET /api/pases/compras/{compra_id}

        Only the buyer (`Compra.responsable`) may read the purchase.

        Raises:
            NotFoundError: the purchase does not exist.
            ForbiddenError: the caller is not the buyer.
        """
        responsable_id = getattr(request.user, "persona_fk_id", None)

        result = await self.orchestrator.obtener_compra(
            compra_id=compra_id,
            responsable_id=responsable_id,
        )

        return success_response(
            PasePresenter.present_compra_estado(result),
            message="Compra de pases encontrada.",
        )

    @route.get(
        "/compras/{compra_id}/beneficiarios",
        response={200: ApiResponse[PaseBeneficiariosListaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def listar_beneficiarios(self, request, compra_id: str):
        """
        List the persons that hold the passes of a purchase.

        Route: GET /api/pases/compras/{compra_id}/beneficiarios

        Only the buyer (`Compra.responsable`) may read the beneficiaries.

        The slot accounting is immutable: a revoked slot stays consumed and
        `slots_disponibles` never grows back after a revocation.

        Raises:
            NotFoundError: the purchase does not exist.
            ForbiddenError: the caller is not the buyer.
        """
        responsable_id = getattr(request.user, "persona_fk_id", None)

        result = await self.orchestrator.listar_beneficiarios(
            compra_id=compra_id,
            responsable_id=responsable_id,
        )

        return success_response(
            PasePresenter.present_beneficiarios_lista(result),
            message="Beneficiarios del pase listados correctamente.",
        )

    @route.post(
        "/compras/{compra_id}/beneficiarios",
        response={200: ApiResponse[PaseBeneficiariosAsignadosOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def asignar_beneficiarios(self, request, compra_id: str, payload: PaseBeneficiariosAsignarIn):
        """
        Assign the persons that receive the passes of a purchase.

        Route: POST /api/pases/compras/{compra_id}/beneficiarios

        The purchase must be PAID and the caller must be the buyer. Each id is
        the UUID of an EXISTING person: the API never creates a person out of
        free text. The slots are immutable: the lowest free ones are used and
        a revoked slot is never restored.

        Raises:
            NotFoundError: the purchase or a person does not exist.
            ForbiddenError: the caller is not the buyer.
            ConflictError: the purchase is not paid, there are not enough free
                slots, a person already holds an active pass in the event or
                the right is not transferable.
        """
        responsable_id = getattr(request.user, "persona_fk_id", None)
        actor_id = getattr(request.auth, "id", None)

        result = await self.orchestrator.asignar_beneficiarios(
            compra_id=compra_id,
            responsable_id=responsable_id,
            actor_id=str(actor_id) if actor_id else None,
            beneficiario_ids=list(payload.beneficiario_ids),
        )

        return success_response(
            PasePresenter.present_beneficiarios_asignados(result),
            message="Beneficiarios del pase asignados correctamente.",
        )

    @route.delete(
        "/compras/{compra_id}/beneficiarios/{persona_id}",
        response={200: ApiResponse[PaseBeneficiarioRevocadoOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def revocar_beneficiario(
        self, request, compra_id: str, persona_id: str, payload: PaseBeneficiarioRevocarIn
    ):
        """
        Revoke the pass of a person, permanently.

        Route: DELETE /api/pases/compras/{compra_id}/beneficiarios/{persona_id}

        The revocation is PERMANENT: the slot is consumed forever and the
        right is never transferred to somebody else. The motive is mandatory
        and the revocation keeps its audit trail.

        Raises:
            NotFoundError: the purchase or the right does not exist.
            ForbiddenError: the caller is not the buyer.
        """
        responsable_id = getattr(request.user, "persona_fk_id", None)
        actor_id = getattr(request.auth, "id", None)

        result = await self.orchestrator.revocar_beneficiario(
            compra_id=compra_id,
            persona_id=persona_id,
            responsable_id=responsable_id,
            actor_id=str(actor_id) if actor_id else None,
            motivo=payload.motivo,
        )

        return success_response(
            PasePresenter.present_beneficiario_revocado(result),
            message="El pase fue revocado correctamente.",
        )
