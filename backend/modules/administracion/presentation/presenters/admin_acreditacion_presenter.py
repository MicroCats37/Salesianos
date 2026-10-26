"""
AdminAcreditacionPresenter — pure transformer of the accreditations and of the
access log.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps result objects
into the typed HTTP wrappers.

`codigo_qr` has NO place in these wrappers: it is a live bearer credential.
"""

from core.pagination import PaginatedData
from modules.administracion.domain.results.admin_acreditacion_results import (
    AdminAccesoListItemResult,
    AdminAcreditacionDetalleResult,
    AdminAcreditacionListItemResult,
)
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.schemas.admin_acreditacion_schemas import (
    AdminAccesoListItemOut,
    AdminAcreditacionDetailOut,
    AdminAcreditacionListItemOut,
)


class AdminAcreditacionPresenter:
    """Transformers of the accreditations and of the access log."""

    @staticmethod
    def present_item(
        result: AdminAcreditacionListItemResult,
    ) -> AdminAcreditacionListItemOut:
        """Map one accreditation into its list wrapper."""
        return AdminAcreditacionListItemOut(
            id=result.id,
            persona_id=result.persona_id,
            persona_nombre=result.persona_nombre,
            persona_documento=result.persona_documento,
            estado=result.estado,
            acceso_fiesta=result.acceso_fiesta,
            acceso_box=result.acceso_box,
            autorizacion_fiesta=result.autorizacion_fiesta,
            habilitado=result.habilitado,
            observacion=result.observacion,
            accesos_permitidos=result.accesos_permitidos,
            ultimo_acceso=result.ultimo_acceso,
        )

    @staticmethod
    def present_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminAcreditacionListItemOut]:
        """Map a page of accreditations into the canonical paginated payload."""
        items = [AdminAcreditacionPresenter.present_item(item) for item in result.items]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    @staticmethod
    def present_detalle(
        result: AdminAcreditacionDetalleResult,
    ) -> AdminAcreditacionDetailOut:
        """Map the drilldown of an accreditation into its wrapper."""
        return AdminAcreditacionDetailOut(
            **AdminAcreditacionPresenter.present_item(result).model_dump(),
            accesos=[
                AdminAcreditacionPresenter.present_acceso(acceso)
                for acceso in result.accesos
            ],
        )

    @staticmethod
    def present_acceso(
        result: AdminAccesoListItemResult,
    ) -> AdminAccesoListItemOut:
        """Map one access record into its wrapper."""
        return AdminAccesoListItemOut(
            id=result.id,
            acreditacion_id=result.acreditacion_id,
            persona_nombre=result.persona_nombre,
            persona_documento=result.persona_documento,
            resultado=result.resultado,
            punto_acceso=result.punto_acceso,
            operador_nombre=result.operador_nombre,
            fecha_hora=result.fecha_hora,
        )

    @staticmethod
    def present_listado_accesos(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminAccesoListItemOut]:
        """Map a page of access records into the canonical paginated payload."""
        items = [
            AdminAcreditacionPresenter.present_acceso(acceso)
            for acceso in result.items
        ]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )


__all__ = ["AdminAcreditacionPresenter"]
