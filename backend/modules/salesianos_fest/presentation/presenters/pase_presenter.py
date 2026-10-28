"""
PasePresenter — transforms domain results to HTTP schemas.

Pure transformer — no DB access, no selectors.
"""
from modules.salesianos_fest.domain.results.pase_results import (
    PaseCatalogoResult,
    PasePrecioCatalogoResult,
    PaseCompraCreadaResult,
    PaseCompraDetalleResult,
    PaseBeneficiarioResult,
    PaseBeneficiariosListaResult,
    PaseBeneficiariosAsignadosResult,
    PaseBeneficiarioRevocadoResult,
)
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    PaseListOut,
    PasePrecioOut,
    PaseCompraCreadaOut,
    PaseCompraEstadoOut,
    PaseBeneficiarioAuditadoOut,
    PaseBeneficiariosListaOut,
    PaseBeneficiariosAsignadosOut,
    PaseBeneficiarioRevocadoOut,
)


class PasePresenter:
    """Transforms PaseCatalogoResult objects to PaseListOut."""

    @staticmethod
    def present_pase_precio(result: PasePrecioCatalogoResult) -> PasePrecioOut:
        """Transform a pass price result.

        Decimal prices are explicitly coerced to float so the JSON response
        emits numeric values (not strings).
        """
        return PasePrecioOut(
            etapa=result.etapa,
            precio_unitario=float(result.precio_unitario),
            vigente_desde=result.vigente_desde,
            vigente_hasta=result.vigente_hasta,
        )

    @staticmethod
    def present_pase(result: PaseCatalogoResult) -> PaseListOut:
        """Transform a pass catalogue result to PaseListOut."""
        return PaseListOut(
            id=result.id,
            evento_id=result.evento_id,
            nombre=result.nombre,
            descripcion=result.descripcion,
            activo=result.activo,
            precio_preventa=(
                float(result.precio_preventa)
                if result.precio_preventa is not None
                else None
            ),
            precio_regular=(
                float(result.precio_regular)
                if result.precio_regular is not None
                else None
            ),
            precio_vigente=(
                float(result.precio_vigente)
                if result.precio_vigente is not None
                else None
            ),
            cantidad_maxima=result.cantidad_maxima,
            precios=[PasePresenter.present_pase_precio(p) for p in result.precios],
        )

    @staticmethod
    def present_pases(results: list[PaseCatalogoResult]) -> list[PaseListOut]:
        """Transform a list of pass catalogue results to PaseListOut list."""
        return [PasePresenter.present_pase(r) for r in results]

    @staticmethod
    def present_compra_creada(result: PaseCompraCreadaResult) -> PaseCompraCreadaOut:
        """Transform a created pass purchase to PaseCompraCreadaOut.

        Decimal amounts are explicitly coerced to float so the JSON response
        emits numeric values (not strings).
        """
        return PaseCompraCreadaOut(
            compra_id=result.compra_id,
            orden_pago_id=result.orden_pago_id,
            numero_orden=result.numero_orden,
            pase_id=result.pase_id,
            pase_nombre=result.pase_nombre,
            cantidad=result.cantidad,
            precio_unitario=float(result.precio_unitario),
            total=float(result.total),
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
        )

    @staticmethod
    def present_compra_estado(result: PaseCompraDetalleResult) -> PaseCompraEstadoOut:
        """Transform the detail of a pass purchase to PaseCompraEstadoOut.

        The internal `responsable_id` is NOT published: it only backs the
        ownership check.
        """
        return PaseCompraEstadoOut(
            compra_id=result.compra_id,
            orden_pago_id=result.orden_pago_id,
            numero_orden=result.numero_orden,
            pase_id=result.pase_id,
            pase_nombre=result.pase_nombre,
            cantidad=result.cantidad,
            precio_unitario=float(result.precio_unitario),
            total=float(result.total),
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            moneda=result.moneda,
            origen_pago=result.origen_pago,
            created_at=result.created_at,
            beneficiarios_asignados=result.beneficiarios_asignados,
            beneficiarios_pendientes=result.beneficiarios_pendientes,
        )

    @staticmethod
    def present_beneficiario(
        result: PaseBeneficiarioResult,
    ) -> PaseBeneficiarioAuditadoOut:
        """Transform a beneficiary result into its audited schema."""
        return PaseBeneficiarioAuditadoOut(
            persona_id=result.persona_id,
            nombre_completo=result.nombre_completo,
            tipo_documento=result.tipo_documento,
            numero_documento=result.numero_documento,
            slot=result.slot,
            estado=result.estado,
            asignado_en=result.asignado_en,
            revocado_en=result.revocado_en,
            motivo_revocacion=result.motivo_revocacion,
        )

    @staticmethod
    def present_beneficiarios(
        results: list[PaseBeneficiarioResult],
    ) -> list[PaseBeneficiarioAuditadoOut]:
        """Transform a list of beneficiary results."""
        return [PasePresenter.present_beneficiario(r) for r in results]

    @staticmethod
    def present_beneficiarios_lista(
        result: PaseBeneficiariosListaResult,
    ) -> PaseBeneficiariosListaOut:
        """Transform the listing of the beneficiaries of a batch."""
        return PaseBeneficiariosListaOut(
            compra_id=result.compra_id,
            cantidad_pases=result.cantidad_pases,
            activos=result.activos,
            revocados=result.revocados,
            slots_usados=result.slots_usados,
            slots_disponibles=result.slots_disponibles,
            beneficiarios=PasePresenter.present_beneficiarios(result.beneficiarios),
        )

    @staticmethod
    def present_beneficiarios_asignados(
        result: PaseBeneficiariosAsignadosResult,
    ) -> PaseBeneficiariosAsignadosOut:
        """Transform the outcome of an assignment of beneficiaries."""
        return PaseBeneficiariosAsignadosOut(
            compra_id=result.compra_id,
            cantidad_pases=result.cantidad_pases,
            activos=result.activos,
            revocados=result.revocados,
            slots_usados=result.slots_usados,
            slots_disponibles=result.slots_disponibles,
            asignados=result.asignados,
            ya_asignados=result.ya_asignados,
            beneficiarios=PasePresenter.present_beneficiarios(result.beneficiarios),
        )

    @staticmethod
    def present_beneficiario_revocado(
        result: PaseBeneficiarioRevocadoResult,
    ) -> PaseBeneficiarioRevocadoOut:
        """Transform the outcome of a permanent revocation."""
        return PaseBeneficiarioRevocadoOut(
            compra_id=result.compra_id,
            cantidad_pases=result.cantidad_pases,
            activos=result.activos,
            revocados=result.revocados,
            slots_usados=result.slots_usados,
            slots_disponibles=result.slots_disponibles,
            persona_id=result.persona_id,
            estado=result.estado,
            revocado_en=result.revocado_en,
            ya_revocado=result.ya_revocado,
        )
