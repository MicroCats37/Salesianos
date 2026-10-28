"""
AdminUsuarioPresenter — pure transformer of the accounts.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps result objects
into the typed HTTP wrappers.

The wrapper declares NO credential: no password, no hash and no token. The tier
of the account (`is_staff`, `is_superuser`, `nivel`) IS published.
"""

from core.pagination import PaginatedData
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.domain.results.admin_usuario_results import (
    AdminUsuarioDetalleResult,
    AdminUsuarioInscripcionResult,
    AdminUsuarioListItemResult,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.schemas.admin_usuario_schemas import (
    AdminUsuarioDetailOut,
    AdminUsuarioInscripcionOut,
    AdminUsuarioListItemOut,
)


class AdminUsuarioPresenter:
    """Transformers of the accounts."""

    @staticmethod
    def present_item(result: AdminUsuarioListItemResult) -> AdminUsuarioListItemOut:
        """Map one account into its list wrapper."""
        return AdminUsuarioListItemOut(
            id=result.id,
            username=result.username,
            email=result.email,
            nombres=result.nombres,
            apellidos=result.apellidos,
            persona_id=result.persona_id,
            persona_documento=result.persona_documento,
            es_admin=result.es_admin,
            is_staff=result.is_staff,
            is_superuser=result.is_superuser,
            nivel=result.nivel,
            is_active=result.is_active,
            last_login=result.last_login,
            created_at=result.created_at,
        )

    @staticmethod
    def present_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminUsuarioListItemOut]:
        """Map a page of accounts into the canonical paginated payload."""
        items = [AdminUsuarioPresenter.present_item(item) for item in result.items]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    @staticmethod
    def present_detalle(result: AdminUsuarioDetalleResult) -> AdminUsuarioDetailOut:
        """Map the drilldown of an account into its wrapper."""
        return AdminUsuarioDetailOut(
            **AdminUsuarioPresenter.present_item(result).model_dump(),
            personas=[
                AdminUsuarioPresenter.present_inscripcion(inscripcion)
                for inscripcion in result.personas
            ],
        )

    @staticmethod
    def present_inscripcion(
        result: AdminUsuarioInscripcionResult,
    ) -> AdminUsuarioInscripcionOut:
        """Map one registration owned by the account into its wrapper."""
        return AdminUsuarioInscripcionOut(
            inscripcion_id=result.inscripcion_id,
            estado=result.estado,
            created_at=result.created_at,
        )


__all__ = ["AdminUsuarioPresenter"]
