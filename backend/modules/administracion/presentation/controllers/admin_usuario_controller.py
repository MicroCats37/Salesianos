"""
AdminUsuarioController — the accounts table and its drilldown (A13, A14).

Thin async controller: payload → orchestrator → presenter → `success_response`
(`contract/django-app-architecture-contract.md` §4.8). No `if`, no ORM, no
manual error response.

Authorization: the whole controller is gated by `RequireUsuariosVer` (the
capability `admin.usuarios.ver`, held by the operational staff and by the
break-glass tier), evaluated SERVER-SIDE on every request: anonymous → 401,
authenticated non-admin → 403, admin → 200.

Routes:
  GET /administracion/usuarios       — the accounts table (A13).
  GET /administracion/usuarios/{id}  — the drilldown (A14).

Both endpoints are READ-ONLY: they never write. The surface never manages
passwords and never exposes a credential. The TIER of every account IS
published (`is_staff`, `is_superuser`, `nivel`) so an account administrator
can see who holds the break-glass tier.
"""
from injector import inject
from ninja import Query
from ninja_extra import api_controller, route

from core.pagination import PaginatedData
from core.permissions import RequireUsuariosVer
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_usuario_presenter import (
    AdminUsuarioPresenter,
)
from modules.administracion.presentation.schemas.admin_usuario_schemas import (
    AdminUsuarioDetailOut,
    AdminUsuarioListItemOut,
)


@api_controller("/administracion", tags=["Administración"], permissions=[RequireUsuariosVer])
class AdminUsuarioController:
    """Controller of the accounts table and its drilldown."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/usuarios",
        response={200: ApiResponse[PaginatedData[AdminUsuarioListItemOut]]},
        auth=JWTAuth(),
    )
    async def listar_usuarios(
        self,
        request,
        page: int | None = Query(None, description="Página (base 1)."),
        page_size: int | None = Query(
            None, description="Elementos por página (máximo 100)."
        ),
        q: str | None = Query(
            None,
            description="Búsqueda sobre usuario, correo, documento y nombre.",
        ),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): created_at, username, nombres, last_login.",
        ),
        estado: str | None = Query(
            None, description="activo o inactivo."
        ),
        es_admin: str | None = Query(
            None, description="true o false: administrador del evento."
        ),
    ):
        """
        Accounts table.

        Route: GET /api/administracion/usuarios

        Authorization: the capability `admin.usuarios.ver` (operational staff
        and break-glass tier).

        The endpoint is READ-ONLY. The response NEVER carries the password,
        its hash nor any token. It DOES publish the tier of the account
        (`is_staff`, `is_superuser`, `nivel`).

        The accounts are global identities: they are NOT scoped to an event.
        The registrations shown in the drilldown (A14) ARE scoped to the
        active event.

        Returns:
            ApiResponse[PaginatedData[AdminUsuarioListItemOut]].
        """
        result = await self.orchestrator.listar_usuarios(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            estado=estado,
            es_admin=es_admin,
        )
        return success_response(AdminUsuarioPresenter.present_listado(result))

    @route.get(
        "/usuarios/{usuario_id}",
        response={200: ApiResponse[AdminUsuarioDetailOut]},
        auth=JWTAuth(),
    )
    async def obtener_usuario(
        self,
        request,
        usuario_id: str,
    ):
        """
        Drilldown of one account.

        Route: GET /api/administracion/usuarios/{usuario_id}

        Authorization: the capability `admin.usuarios.ver` (operational staff
        and break-glass tier).

        The endpoint is READ-ONLY and returns the account with the
        registrations it owns INSIDE the active event. The response NEVER
        carries the password, its hash nor any token. It DOES publish the tier
        of the account (`is_staff`, `is_superuser`, `nivel`).

        An unknown id is answered with 404 `RESOURCE_NOT_FOUND`.

        Returns:
            ApiResponse[AdminUsuarioDetailOut].
        """
        result = await self.orchestrator.obtener_usuario_detalle(usuario_id)
        return success_response(AdminUsuarioPresenter.present_detalle(result))


__all__ = ["AdminUsuarioController"]
