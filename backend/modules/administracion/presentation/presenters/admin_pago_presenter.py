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
    AdminAprobacionManualResult,
    AdminPagoAnularManualResult,
    AdminPagoAprobarManualResult,
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
    AdminPaseBeneficiarioResult,
    AdminTransaccionListItemResult,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminAprobacionManualOut,
    AdminPagoAnularManualOut,
    AdminPagoAprobarManualOut,
    AdminPagoDetailOut,
    AdminPagoListItemOut,
    AdminPaseBeneficiarioOut,
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
            pase_id=result.pase_id,
            responsable_nombre=result.responsable_nombre,
            tipo=result.tipo,
            producto_nombre=result.producto_nombre,
            cantidad=result.cantidad,
            precio_unitario=result.precio_unitario,
            total=result.total,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            pagada_en=result.pagada_en,
            origen_pago=result.origen_pago,
            monto_orden=result.monto_orden,
            moneda_orden=result.moneda_orden,
            beneficiarios_activos=result.beneficiarios_activos,
            beneficiarios_revocados=result.beneficiarios_revocados,
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
            aprobaciones=[
                AdminPagoPresenter.present_aprobacion(aprobacion)
                for aprobacion in result.aprobaciones
            ],
            beneficiarios=[
                AdminPagoPresenter.present_beneficiario(beneficiario)
                for beneficiario in result.beneficiarios
            ],
        )

    @staticmethod
    def present_beneficiario(
        result: AdminPaseBeneficiarioResult,
    ) -> AdminPaseBeneficiarioOut:
        """Map one nominative right into its wrapper (no names, no QR)."""
        return AdminPaseBeneficiarioOut(
            persona_id=result.persona_id,
            slot=result.slot,
            estado=result.estado,
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

    @staticmethod
    def present_aprobacion(
        result: AdminAprobacionManualResult,
    ) -> AdminAprobacionManualOut:
        """Map one entry of the manual approval history into its wrapper."""
        return AdminAprobacionManualOut(
            id=result.id,
            estado=result.estado,
            canal=result.canal,
            referencia=result.referencia,
            monto=result.monto,
            moneda=result.moneda,
            motivo=result.motivo,
            actor=result.actor,
            anulada_por=result.anulada_por,
            anulada_en=result.anulada_en,
            motivo_anulacion=result.motivo_anulacion,
            created_at=result.created_at,
        )

    @staticmethod
    def present_aprobar_manual(
        result: AdminPagoAprobarManualResult,
    ) -> AdminPagoAprobarManualOut:
        """Map the outcome of the manual approval into its wrapper."""
        return AdminPagoAprobarManualOut(
            resultado=result.resultado,
            settlement_status=result.settlement_status,
            orden_pago_id=result.orden_pago_id,
            numero_orden=result.numero_orden,
            estado_orden=result.estado_orden,
            aprobacion_id=result.aprobacion_id,
            estado_aprobacion=result.estado_aprobacion,
            canal=result.canal,
            referencia=result.referencia,
            monto=result.monto,
            moneda=result.moneda,
            motivo=result.motivo,
            actor=result.actor,
            approved_at=result.approved_at,
        )

    @staticmethod
    def present_anular_manual(
        result: AdminPagoAnularManualResult,
    ) -> AdminPagoAnularManualOut:
        """Map the outcome of the manual annulment into its wrapper."""
        return AdminPagoAnularManualOut(
            resultado=result.resultado,
            orden_pago_id=result.orden_pago_id,
            compra_id=result.compra_id,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            estado_aprobacion=result.estado_aprobacion,
            asignaciones_revocadas=result.asignaciones_revocadas,
            beneficiarios_revocados=result.beneficiarios_revocados,
            personas_afectadas=result.personas_afectadas,
            anulada_por=result.anulada_por,
            anulada_en=result.anulada_en,
            motivo_anulacion=result.motivo_anulacion,
        )


__all__ = ["AdminPagoPresenter"]
