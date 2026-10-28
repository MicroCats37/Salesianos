"""
AdminOperacionController — the teams, the participants, the roster rows, the
accreditations and the access log (A7–A12).

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireAdminVer`
(the capability `admin.ver`, held by the operational staff and by the
break-glass tier, evaluated SERVER-SIDE on every request):
anonymous → 401, authenticated non-admin → 403, admin → 200.

Routes:
  GET /administracion/equipos            — the teams (A7).
  GET /administracion/participantes      — the registered people (A8).
  GET /administracion/participaciones    — the roster rows (A9).
  GET /administracion/acreditaciones     — the accreditations (A10).
  GET /administracion/acreditaciones/{id} — the drilldown of an accreditation (A11).
  GET /administracion/accesos            — the access log (A12).

Every endpoint is READ-ONLY: they never write.
"""
from injector import inject
from ninja import Query
from ninja_extra import api_controller, route

from core.pagination import PaginatedData
from core.permissions import RequireAdminVer
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_acreditacion_presenter import (
    AdminAcreditacionPresenter,
)
from modules.administracion.presentation.presenters.admin_inscripcion_presenter import (
    AdminInscripcionPresenter,
)
from modules.administracion.presentation.schemas.admin_acreditacion_schemas import (
    AdminAccesoListItemOut,
    AdminAcreditacionDetailOut,
    AdminAcreditacionListItemOut,
)
from modules.administracion.presentation.schemas.admin_inscripcion_schemas import (
    AdminEquipoListItemOut,
    AdminParticipacionListItemOut,
    AdminParticipanteListItemOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireAdminVer])
class AdminOperacionController:
    """Controller of the operational tables of the event."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/equipos",
        response={200: ApiResponse[PaginatedData[AdminEquipoListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_equipos(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(None, description="Búsqueda sobre el nombre del equipo."),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): created_at, nombre, disciplina, estado.",
        ),
        inscripcion_id: str | None = Query(
            None, description="Inscripción (UUID)."
        ),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        estado: str | None = Query(None, description="Estado del equipo."),
        roster: str | None = Query(
            None, description="Estado del plantilla: COMPLETO o INCOMPLETO."
        ),
    ):
        """
        Teams table of the active event.

        Route: GET /api/administracion/equipos

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The roster state (COMPLETO / INCOMPLETO) is
        DERIVED on the server: a team is complete when its ACTIVE
        participations reach the `min_jugadores` of its discipline.

        Returns:
            ApiResponse[PaginatedData[AdminEquipoListItemOut]].
        """
        result = await self.orchestrator.listar_equipos(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            inscripcion_id=inscripcion_id,
            disciplina_id=disciplina_id,
            estado=estado,
            roster=roster,
        )
        return success_response(AdminInscripcionPresenter.present_equipo_listado(result))

    @route.get(
        "/participantes",
        response={200: ApiResponse[PaginatedData[AdminParticipanteListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_participantes(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(None, description="Búsqueda sobre la persona."),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): created_at, persona, estado.",
        ),
        estado_pool: str | None = Query(
            None,
            description=(
                "Estado del pool: LISTO, ESPERANDO_PAGO, SIN_CAPACIDAD, "
                "CUPO_POR_ASIGNAR."
            ),
        ),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        con_cupo: str | None = Query(
            None, description="true o false: con cupo activo."
        ),
    ):
        """
        Registered people of the active event.

        Route: GET /api/administracion/participantes

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. This is the POOL surface: the people
        registered in an inscription. The pool state is DERIVED on the server
        from the paid capacity of the registration and the cup assignment of
        the person — it is never persisted and never re-derived by the client.

        People and roster rows are two different numbers: one paid cup
        authorises a person in EVERY contracted discipline.

        Returns:
            ApiResponse[PaginatedData[AdminParticipanteListItemOut]].
        """
        result = await self.orchestrator.listar_participantes(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            estado_pool=estado_pool,
            disciplina_id=disciplina_id,
            con_cupo=con_cupo,
        )
        return success_response(
            AdminInscripcionPresenter.present_participante_listado(result)
        )

    @route.get(
        "/participaciones",
        response={200: ApiResponse[PaginatedData[AdminParticipacionListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_participaciones(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(
            None, description="Búsqueda sobre la persona y el equipo."
        ),
        ordering: str | None = Query(
            None,
            description=(
                "Orden (lista blanca): created_at, persona, equipo, disciplina, "
                "rol, estado."
            ),
        ),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        rol: str | None = Query(None, description="Rol: J, C o D."),
        estado: str | None = Query(None, description="Estado: A o R."),
        inscripcion_id: str | None = Query(
            None, description="Inscripción (UUID)."
        ),
    ):
        """
        Roster rows of the active event.

        Route: GET /api/administracion/participaciones

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. This is the ROSTER surface: one person
        placed in one team of one discipline. It is NOT the people list: the
        two numbers are different by design.

        Returns:
            ApiResponse[PaginatedData[AdminParticipacionListItemOut]].
        """
        result = await self.orchestrator.listar_participaciones(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            disciplina_id=disciplina_id,
            rol=rol,
            estado=estado,
            inscripcion_id=inscripcion_id,
        )
        return success_response(
            AdminInscripcionPresenter.present_participacion_listado(result)
        )

    @route.get(
        "/acreditaciones",
        response={200: ApiResponse[PaginatedData[AdminAcreditacionListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_acreditaciones(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(None, description="Búsqueda sobre la persona."),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): persona, estado, autorizacion_fiesta.",
        ),
        estado: str | None = Query(None, description="Estado de la acreditación."),
        autorizacion_fiesta: str | None = Query(
            None,
            description="AUTOMATICA, AUTORIZADA o BLOQUEADA.",
        ),
        acceso_fiesta: str | None = Query(
            None, description="true o false: acceso a fiesta."
        ),
    ):
        """
        Accreditations of the active event.

        Route: GET /api/administracion/acreditaciones

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The response NEVER carries `codigo_qr`:
        the QR code is a live bearer credential and is delivered only by the
        explicit, admin-only QR generation action of the owning module.

        Returns:
            ApiResponse[PaginatedData[AdminAcreditacionListItemOut]].
        """
        result = await self.orchestrator.listar_acreditaciones(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            estado=estado,
            autorizacion_fiesta=autorizacion_fiesta,
            acceso_fiesta=acceso_fiesta,
        )
        return success_response(AdminAcreditacionPresenter.present_listado(result))

    @route.get(
        "/acreditaciones/{acreditacion_id}",
        response={200: ApiResponse[AdminAcreditacionDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_acreditacion(
        self,
        request,
        acreditacion_id: str,
    ):
        """
        Drilldown of one accreditation of the active event.

        Route: GET /api/administracion/acreditaciones/{acreditacion_id}

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and returns the accreditation with its
        access records. The response NEVER carries `codigo_qr`.

        An unknown id AND an id of another edition are answered the SAME way:
        404 `RESOURCE_NOT_FOUND`.

        Returns:
            ApiResponse[AdminAcreditacionDetailOut].
        """
        result = await self.orchestrator.obtener_acreditacion_detalle(acreditacion_id)
        return success_response(AdminAcreditacionPresenter.present_detalle(result))

    @route.get(
        "/accesos",
        response={200: ApiResponse[PaginatedData[AdminAccesoListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_accesos(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(None, description="Búsqueda sobre la persona."),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): fecha_hora, resultado, punto_acceso.",
        ),
        resultado: str | None = Query(None, description="PERMITIDO o DENEGADO."),
        punto_acceso: str | None = Query(None, description="Punto de acceso."),
        desde: str | None = Query(None, description="Fecha inicial (ISO)."),
        hasta: str | None = Query(None, description="Fecha final (ISO)."),
    ):
        """
        Access log of the active event.

        Route: GET /api/administracion/accesos

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY and returns the attempts recorded by the
        scanners, newest first by default.

        Returns:
            ApiResponse[PaginatedData[AdminAccesoListItemOut]].
        """
        result = await self.orchestrator.listar_accesos(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            resultado=resultado,
            punto_acceso=punto_acceso,
            desde=desde,
            hasta=hasta,
        )
        return success_response(AdminAcreditacionPresenter.present_listado_accesos(result))


__all__ = ["AdminOperacionController"]
