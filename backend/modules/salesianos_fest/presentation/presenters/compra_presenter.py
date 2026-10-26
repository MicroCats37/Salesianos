"""
CompraPresenter — transforms Compra domain results into HTTP schemas.

Now operates on commerce.Compra + CompraInscripcion composition.
"""
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.results.compra_results import (
    CompraCreatedResult,
    CompraIzipayPreparedResult,
    CompraConfirmedResult,
    CompraCanceladaResult,
)
from modules.salesianos_fest.presentation.schemas.compra_schemas import (
    CompraCreateOut,
    CompraDetailOut,
    CompraListOut,
    IniciarPagoOut,
    ConfirmarPagoOut,
    CompraCanceladaOut,
)


class CompraPresenter:
    """Transforms Compra domain results into HTTP output schemas."""

    @staticmethod
    def present_created(
        result: CompraCreatedResult,
        message: str = "Compra creada correctamente.",
    ) -> CompraCreateOut:
        """Transform CompraCreatedResult into CompraCreateOut."""
        return CompraCreateOut(
            compra_id=result.compra_id,
            compra_inscripcion_id=result.compra_inscripcion_id,
            orden_pago_id=result.orden_pago_id,
            tipo=result.tipo,
            cantidad=result.cantidad,
            precio_unitario=result.precio_unitario,
            total=result.total,
            estado=result.estado,
            message=message,
        )

    @staticmethod
    def present_detail(compra: Compra) -> CompraDetailOut:
        """Transform a commerce.Compra model instance into CompraDetailOut."""
        compra_inscripcion = getattr(compra, "compra_inscripcion", None)
        inscripcion_id = ""
        if compra_inscripcion:
            inscripcion_id = str(compra_inscripcion.inscripcion_id)
        return CompraDetailOut(
            id=str(compra.id),
            inscripcion_id=inscripcion_id,
            orden_pago_id=str(compra.orden_pago_id) if compra.orden_pago_id else "",
            tipo=compra_inscripcion.tipo if compra_inscripcion else "",
            cantidad=compra_inscripcion.cantidad if compra_inscripcion else 0,
            precio_unitario=compra_inscripcion.precio_unitario if compra_inscripcion else compra.total,
            total=compra.total,
            estado=compra.estado,
            created_at=compra.created_at.isoformat(),
        )

    @staticmethod
    def present_list(compras: list[Compra]) -> CompraListOut:
        """Transform a list of commerce.Compra models into CompraListOut."""
        return CompraListOut(
            compras=[CompraPresenter.present_detail(c) for c in compras]
        )

    @staticmethod
    def present_iniciar_pago(
        result: CompraIzipayPreparedResult,
    ) -> IniciarPagoOut:
        """Transform CompraIzipayPreparedResult into IniciarPagoOut."""
        return IniciarPagoOut(
            compra_id=result.compra_id,
            orden_pago_id=result.orden_pago_id,
            transaction_id=result.transaction_id,
            order_number=result.order_number,
            token=result.token,
            merchant_code=result.merchant_code,
            amount=result.amount,
            currency=result.currency,
            buyer_email=result.buyer_email,
            buyer_name=result.buyer_name,
            buyer_surname=result.buyer_surname,
        )

    @staticmethod
    def present_confirmar(
        result: CompraConfirmedResult,
    ) -> ConfirmarPagoOut:
        """Transform CompraConfirmedResult into ConfirmarPagoOut."""
        return ConfirmarPagoOut(
            compra_id=result.compra_id,
            success=result.success,
            already_confirmed=result.already_confirmed,
        )

    @staticmethod
    def present_cancelar(
        result: CompraCanceladaResult,
    ) -> CompraCanceladaOut:
        """Transform CompraCanceladaResult into CompraCanceladaOut."""
        return CompraCanceladaOut(
            compra_id=result.compra_id,
            inscripcion_id=result.inscripcion_id,
            estado=result.estado,
            ya_cancelada=result.ya_cancelada,
            asignaciones_revocadas=result.asignaciones_revocadas,
            personas_afectadas=result.personas_afectadas,
        )
