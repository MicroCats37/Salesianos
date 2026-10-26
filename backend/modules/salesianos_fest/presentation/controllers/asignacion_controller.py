"""
AsignacionController — AsignacionCupo quota assignment endpoints.

Thin async controller — only delegates to AsignacionOrchestrator.
Authentication required for all operations.

Routes:
  POST /api/asignaciones/                       - Assign quota to a registered person
  GET  /api/asignaciones/{asignacion_id}        - Get asignacion detail
  GET  /api/inscripciones/{id}/asignaciones    - List asignaciones for inscripcion
  POST /api/asignaciones/liberar                - Liberate a player's cupo
  GET  /api/inscripciones/{id}/saldo            - Get saldo: contratados/pagados/asignados/disponibles
"""
from asgiref.sync import sync_to_async
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from core.exceptions import BusinessError, NotFoundError
from modules.salesianos_fest.domain.services.orchestrators.asignacion_orchestrator import AsignacionOrchestrator
from modules.salesianos_fest.domain.selectors.asignacion_selector import AsignacionSelector
from modules.salesianos_fest.presentation.schemas.asignacion_schemas import (
    AsignarPersonaIn,
    AsignarPersonaOut,
    LiberarCupoIn,
    LiberarCupoOut,
    SaldoOut,
    AsignacionDetailOut,
    AsignacionListOut,
)
from modules.salesianos_fest.presentation.presenters.asignacion_presenter import AsignacionPresenter
from modules.salesianos_fest.presentation.ownership import (
    check_ownership_or_admin,
    check_ownership_or_admin_for_asignacion,
)


def _get_authenticated_persona_id(request) -> str:
    """Extract persona_id from the authenticated request."""
    user = request.user
    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise BusinessError("Usuario sin persona vinculada. Complete su registro.")
    return str(persona_id)


@api_controller("/asignaciones", tags=["Asignaciones"], permissions=[IsAuthenticated])
class AsignacionController:
    """
    Controller for AsignacionCupo quota assignment operations.
    """

    @inject
    def __init__(
        self,
        orchestrator: AsignacionOrchestrator,
        selector: AsignacionSelector,
    ):
        self.orchestrator = orchestrator
        self.selector = selector

    @route.post(
        "/",
        response={200: ApiResponse[AsignarPersonaOut]},
        auth=JWTAuth(),
    )
    async def asignar_persona(self, request, payload: AsignarPersonaIn):
        """
        Assign a person to an inscripcion if saldo disponible > 0.

        Route: POST /api/asignaciones/

        Creates AsignacionCupo for the registered person.

        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser). Consuming the paid capacity of somebody
        else's inscripcion is never allowed.

        Raises:
            BusinessError: if user has no Persona.
            ForbiddenError: if the user is not the responsable nor an admin.
            NotFoundError: if inscripcion not found.
            ConflictError: if no saldo disponible or person already assigned.
        """
        await check_ownership_or_admin(request, str(payload.inscripcion_id))

        result = await self.orchestrator.asignar_persona(
            inscripcion_id=str(payload.inscripcion_id),
            persona_id=str(payload.persona_id),
        )
        return success_response(
            AsignacionPresenter.present_asignar_persona({
                "asignacion_id": result.asignacion_id,
                "inscripcion_id": result.inscripcion_id,
                "persona_id": result.persona_id,
                "estado": result.estado,
                "compra_origen_id": result.compra_origen_id,
            }),
            message="Persona asignada correctamente.",
        )

    @route.post(
        "/liberar",
        response={200: ApiResponse[LiberarCupoOut]},
        auth=JWTAuth(),
    )
    async def liberar_cupo(self, request, payload: LiberarCupoIn):
        """
        Liberate a player's cupo from an inscripcion.

        Route: POST /api/asignaciones/liberar

        Marks Participacion as RETIRADA and AsignacionCupo as LIBERADA.

        `disciplina_id` scopes the release to ONE discipline: only the
        participations of that discipline are retired, and the paid cup
        SURVIVES while the person keeps an active participation in another
        discipline of the same inscripcion (one cup, several disciplines).

        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).

        Raises:
            BusinessError: if user has no Persona.
            ForbiddenError: if the user is not the responsable nor an admin.
        """
        await check_ownership_or_admin(request, str(payload.inscripcion_id))

        result = await self.orchestrator.liberar_cupo(
            inscripcion_id=str(payload.inscripcion_id),
            persona_id=str(payload.persona_id),
            motivo=payload.motivo,
            disciplina_id=payload.disciplina_id,
        )
        return success_response(
            AsignacionPresenter.present_liberar_cupo({
                "inscripcion_id": result.inscripcion_id,
                "persona_id": result.persona_id,
                "asignacion_id": result.asignacion_id,
                "estado": result.estado,
                "cupo_liberado": result.estado == "LIBERADA",
            }),
            message="Cupo liberado correctamente."
            if result.estado == "LIBERADA"
            else "Participaciones retiradas. El cupo se mantiene mientras la persona juegue en otra disciplina.",
        )

    @route.get(
        "/{asignacion_id}",
        response={200: ApiResponse[AsignacionDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_asignacion(self, request, asignacion_id: str):
        """
        Get AsignacionCupo detail by ID.

        Route: GET /api/asignaciones/{asignacion_id}

        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser). The asignacion exposes the inscription, the
        person and the cup, so it never leaves the owner's scope.

        Raises:
            NotFoundError: if asignacion not found.
        """
        await check_ownership_or_admin_for_asignacion(request, asignacion_id)
        asignacion = await self._sync_call(self.selector.obtener_por_id, asignacion_id)
        if not asignacion:
            raise NotFoundError(
                f"Asignacion {asignacion_id} no encontrada.",
                code="ASIGNACION_NOT_FOUND",
            )
        return success_response(
            AsignacionPresenter.present_detail(asignacion),
            message="Asignacion encontrada.",
        )

    @route.get(
        "/inscripciones/{inscripcion_id}/asignaciones",
        response={200: ApiResponse[AsignacionListOut]},
        auth=JWTAuth(),
    )
    async def listar_asignaciones_inscripcion(self, request, inscripcion_id: str):
        """
        List all asignaciones for an inscripcion.

        Route: GET /api/asignaciones/inscripciones/{inscripcion_id}/asignaciones

        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).

        Raises:
            NotFoundError: if inscripcion not found.
        """
        await check_ownership_or_admin(request, inscripcion_id)
        asignaciones = await self._sync_call(
            self.selector.listar_por_inscripcion, inscripcion_id
        )
        return success_response(
            AsignacionPresenter.present_list(asignaciones),
            message="Asignaciones encontradas.",
        )

    async def _sync_call(self, func, *args, **kwargs):
        """Helper to call a sync function in an async context."""
        return await sync_to_async(func)(*args, **kwargs)


@api_controller("/inscripciones", tags=["Inscripciones"], permissions=[IsAuthenticated])
class InscripcionSaldoController:
    """
    Controller for saldo queries.
    """

    @inject
    def __init__(self, orchestrator: "AsignacionOrchestrator"):
        self.orchestrator = orchestrator

    @route.get(
        "/{inscripcion_id}/saldo",
        response={200: ApiResponse[SaldoOut]},
        auth=JWTAuth(),
    )
    async def obtener_saldo(self, request, inscripcion_id: str):
        """
        Get saldo for an inscripcion.

        Route: GET /api/inscripciones/{inscripcion_id}/saldo

        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser). El saldo expone el balance comercial de la
        inscripción.

        Returns: contratados/pagados/asignados_pagados/disponibles_pagados
        """
        await check_ownership_or_admin(request, inscripcion_id)
        saldo = await self.orchestrator.obtener_saldo(inscripcion_id)
        return success_response(
            AsignacionPresenter.present_saldo(saldo),
            message="Saldo calculado.",
        )
