"""
AcreditacionController — AcreditacionEvento accreditation and QR access endpoints.

Thin async controller — only delegates to AcreditacionOrchestrator.

Routes:
  GET  /api/acreditaciones/{evento_id}/{persona_id}   - Get accreditation status
  PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta - Admin override
  POST /api/acreditaciones/{evento_id}/{persona_id}/generar-qr - Regenerate QR code
  POST /api/acceso/registrar                              - Register QR scan access
"""
from asgiref.sync import sync_to_async
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from core.exceptions import NotFoundError
from core.permissions import RequireAcreditacionesEscribir
from modules.salesianos_fest.domain.services.orchestrators.acreditacion_orchestrator import AcreditacionOrchestrator
from modules.salesianos_fest.domain.selectors.acreditacion_selector import AcreditacionSelector
from modules.salesianos_fest.presentation.schemas.acreditacion_schemas import (
    AcreditacionOut,
    OverrideFiestaIn,
    OverrideFiestaOut,
    GenerarQROut,
    RegistrarAccesoIn,
    RegistrarAccesoOut,
)
from modules.salesianos_fest.presentation.presenters.acreditacion_presenter import AcreditacionPresenter
from modules.salesianos_fest.presentation.ownership import check_acreditacion_access_or_admin


@api_controller("/acreditaciones", tags=["Acreditaciones"], permissions=[IsAuthenticated])
class AcreditacionController:
    """
    Controller for AcreditacionEvento accreditation operations.
    """

    @inject
    def __init__(
        self,
        orchestrator: AcreditacionOrchestrator,
        selector: AcreditacionSelector,
    ):
        self.orchestrator = orchestrator
        self.selector = selector

    @route.get(
        "/{evento_id}/{persona_id}",
        response={200: ApiResponse[AcreditacionOut]},
        auth=JWTAuth(),
    )
    async def obtener_acreditacion(self, request, evento_id: str, persona_id: str):
        """
        Get accreditation status for an evento/persona.

        Route: GET /api/acreditaciones/{evento_id}/{persona_id}

        Authorization: the accredited person OR a Django admin
        (is_staff/is_superuser).

        The live QR credential (`codigo_qr`) is NOT part of this payload: it is
        a bearer credential and is delivered only by the explicit, admin-only
        QR generation action (`POST .../generar-qr`).

        Raises:
            NotFoundError: if acreditacion not found.
        """
        await check_acreditacion_access_or_admin(request, persona_id)
        acreditacion = await self._sync_call(
            self.selector.obtener_por_evento_persona, evento_id, persona_id
        )
        if not acreditacion:
            raise NotFoundError(
                f"Acreditacion no encontrada para este evento y persona.",
                code="ACREDITACION_NOT_FOUND",
            )
        return success_response(
            AcreditacionPresenter.present_acreditacion(acreditacion),
            message="Acreditacion encontrada.",
        )

    @route.patch(
        "/{evento_id}/{persona_id}/override-fiesta",
        response={200: ApiResponse[OverrideFiestaOut]},
        auth=JWTAuth(),
        permissions=[RequireAcreditacionesEscribir],
    )
    async def override_fiesta(self, request, evento_id: str, persona_id: str, payload: OverrideFiestaIn):
        """
        Admin override for fiesta access.

        Route: PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta

        Sets autorizacion_fiesta to AUTORIZADA or BLOQUEADA.
        The override persists and takes precedence over AUTOMATICA.

        Authorization: the capability `admin.acreditaciones.escribir` (the
        operational staff and the break-glass tier). Anonymous callers get
        401; authenticated non-admins get 403 and nothing is mutated.

        Raises:
            ValueError: if autorizacion is invalid.
        """
        result = await self.orchestrator.aplicar_override_fiesta(
            evento_id=evento_id,
            persona_id=persona_id,
            autorizacion=payload.autorizacion,
            motivo=payload.motivo,
        )
        return success_response(
            AcreditacionPresenter.present_override({
                "persona_id": result.persona_id,
                "evento_id": result.evento_id,
                "autorizacion_fiesta": result.autorizacion_fiesta,
                "acceso_fiesta": result.acceso_fiesta,
                "observacion": result.observacion,
            }),
            message="Override de fiesta aplicado.",
        )

    @route.post(
        "/{evento_id}/{persona_id}/generar-qr",
        response={200: ApiResponse[GenerarQROut]},
        auth=JWTAuth(),
        permissions=[RequireAcreditacionesEscribir],
    )
    async def generar_qr(self, request, evento_id: str, persona_id: str):
        """
        Regenerate QR code for an acreditacion.

        Route: POST /api/acreditaciones/{evento_id}/{persona_id}/generar-qr

        This is the ONLY endpoint that delivers the live QR credential, and
        it needs the capability `admin.acreditaciones.escribir` (the
        operational staff and the break-glass tier). The previous credential stops
        working as soon as it is rotated.

        Raises:
            NotFoundError: if acreditacion not found.
        """
        result = await self.orchestrator.regenerar_qr(evento_id, persona_id)
        if result is None:
            raise NotFoundError(
                f"Acreditacion no encontrada para este evento y persona.",
                code="ACREDITACION_NOT_FOUND",
            )

        return success_response(
            AcreditacionPresenter.present_generar_qr(result),
            message="Codigo QR regenerado.",
        )

    async def _sync_call(self, func, *args, **kwargs):
        """Helper to call a sync function in an async context."""
        return await sync_to_async(func)(*args, **kwargs)


@api_controller("/acceso", tags=["Acceso"], permissions=[IsAuthenticated])
class AccesoController:
    """
    Controller for QR scan access registration.
    """

    @inject
    def __init__(self, orchestrator: AcreditacionOrchestrator):
        self.orchestrator = orchestrator

    @route.post(
        "/registrar",
        response={200: ApiResponse[RegistrarAccesoOut]},
        auth=JWTAuth(),
    )
    async def registrar_acceso(self, request, payload: RegistrarAccesoIn):
        """
        Register an access attempt via QR scan.

        Route: POST /api/acceso/registrar

        Single-use per event day.

        Raises:
            NotFoundError: if QR code not found.
            ConflictError: if QR already used today.
        """
        operador_id = request.user.id if request.user.is_authenticated else None
        result = await self.orchestrator.registrar_acceso(
            qr_token=payload.qr_token,
            punto_acceso=payload.punto_acceso,
            operador_id=operador_id,
        )
        return success_response(
            AcreditacionPresenter.present_registrar_acceso({
                "resultado": result.resultado,
                "persona_nombre": result.persona_nombre,
                "acceso_fiesta": result.acceso_fiesta,
                "timestamp": result.timestamp,
            }),
            message="Acceso registrado."
            if result.resultado == "PERMITIDO"
            else "Acceso denegado.",
        )
