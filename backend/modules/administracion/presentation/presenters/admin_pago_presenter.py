"""
AdminPagoPresenter — pure transformer of the payments.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps result objects
into the typed HTTP wrappers.

The wrapper declares NO credential: the restricted blobs of the payment module
(`metadata`, `token_sesion`, `response_message`, `transaction_id`) are not
even part of the result DTOs, so they can never be serialized.
"""

from core.pagination import PaginatedData
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.domain.results.admin_pago_results import (
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
    AdminTransaccionListItemResult,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminPagoDetailOut,
    AdminPagoListItemOut,
    AdminTransaccionListItemOut,
)


class AdminPagoPresenter:
    """Transformers of the payments."""

    @staticmethod
    def present_item(result: AdminPagoListItemResult) -> AdminPagoListItemOut:
        """Map one purchase into its list wrapper."""
        return AdminPagoListItemOut(
            compra_id=result.compra_id,
            orden_pago_id=result.orden_pago_id,
            numero_orden=result.numero_orden,
            inscripcion_id=result.inscripcion_id,
            responsable_nombre=result.responsable_nombre,
            tipo=result.tipo,
            cantidad=result.cantidad,
            precio_unitario=result.precio_unitario,
            total=result.total,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            pagada_en=result.pagada_en,
            created_at=result.created_at,
        )

    @staticmethod
    def present_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminPagoListItemOut]:
        """Map a page of purchases into the canonical paginated payload."""
        items = [AdminPagoPresenter.present_item(item) for item in result.items]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    @staticmethod
    def present_detalle(result: AdminPagoDetalleResult) -> AdminPagoDetailOut:
        """Map the drilldown of a payment order into its wrapper."""
        return AdminPagoDetailOut(
            **AdminPagoPresenter.present_item(result).model_dump(),
            transacciones=[
                AdminPagoPresenter.present_transaccion(transaccion)
                for transaccion in result.transacciones
            ],
        )

    @staticmethod
    def present_transaccion(
        result: AdminTransaccionListItemResult,
    ) -> AdminTransaccionListItemOut:
        """Map one payment attempt into its wrapper (explicit fields only)."""
        return AdminTransaccionListItemOut(
            id=result.id,
            status=result.status,
            amount=result.amount,
            currency=result.currency,
            metodo_pago=result.metodo_pago,
            response_code=result.response_code,
            created_at=result.created_at,
        )


__all__ = ["AdminPagoPresenter"]
