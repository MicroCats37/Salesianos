"""Presenters de los BENEFICIARIOS de un lote de pases.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-RT-1.0.0`
Ledger: `RT-PS-03` (`PaseCompraDetallePresenter` → `PaseCompraDetalleOut`) ·
        `RT-PS-04` (`PaseBeneficiariosPresenter` → `PaseBeneficiariosOut`) ·
        `RT-PS-05` (`PaseBeneficiarioAsignarPresenter` →
        `PaseBeneficiariosOut`) ·
        `RT-RT-03` (`PaseBeneficiarioPresenter` →
        `PaseBeneficiarioRevocadoOut`)
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

Los presenters son TRANSFORMADORES PUROS: no consultan la base de datos y no
construyen mensajes públicos de error.

La aritmética la hace el SERVIDOR: el wrapper lleva los TRES números
(`cantidad`, `asignados`, `disponibles`) y el cliente nunca resta.
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.pase_result import (
    PaseBeneficiarioRevocadoResult,
    PaseBeneficiarioResult,
    PaseBeneficiariosResult,
    PaseCompraDetalleResult,
)
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    PaseBeneficiarioOut,
    PaseBeneficiarioRevocadoOut,
    PaseBeneficiariosOut,
    PaseCompraDetalleOut,
)


class PaseBeneficiariosPresenter:
    """Transformador del listado de derechos de un lote."""

    @staticmethod
    def present_beneficiarios(
        result: PaseBeneficiariosResult,
    ) -> PaseBeneficiariosOut:
        """Proyecta los derechos del lote al wrapper HTTP."""
        return PaseBeneficiariosOut(
            compra_pase_id=UUID(result.compra_pase_id),
            estado=result.estado,
            cantidad=result.cantidad,
            asignados=result.asignados,
            disponibles=result.disponibles,
            beneficiarios=[
                PaseBeneficiariosPresenter._present_beneficiario(beneficiario)
                for beneficiario in result.beneficiarios
            ],
        )

    @staticmethod
    def _present_beneficiario(
        beneficiario: PaseBeneficiarioResult,
    ) -> PaseBeneficiarioOut:
        """Proyecta un derecho de entrada."""
        return PaseBeneficiarioOut(
            id=UUID(beneficiario.id),
            pase_id=UUID(beneficiario.pase_id),
            pase_nombre=beneficiario.pase_nombre,
            edicion_id=UUID(beneficiario.edicion_id),
            persona_id=UUID(beneficiario.persona_id),
            persona_nombres=beneficiario.persona_nombres,
            persona_apellidos=beneficiario.persona_apellidos,
            persona_tipo_documento=beneficiario.persona_tipo_documento,
            persona_numero_documento=beneficiario.persona_numero_documento,
            origen=beneficiario.origen,
            estado=beneficiario.estado,
            cantidad=beneficiario.cantidad,
            cantidad_consumida=beneficiario.cantidad_consumida,
            cantidad_disponible=beneficiario.cantidad_disponible,
            asignado_en=beneficiario.asignado_en,
            motivo=beneficiario.motivo,
            revocado_en=beneficiario.revocado_en,
            motivo_revocacion=beneficiario.motivo_revocacion,
        )


class PaseCompraDetallePresenter:
    """Transformador del detalle de la compra de un lote."""

    @staticmethod
    def present_detalle(result: PaseCompraDetalleResult) -> PaseCompraDetalleOut:
        """Proyecta el detalle de la compra al wrapper HTTP."""
        return PaseCompraDetalleOut(
            compra_pase_id=UUID(result.compra_pase_id),
            estado=result.estado,
            cantidad=result.cantidad,
            asignados=result.asignados,
            disponibles=result.disponibles,
            beneficiarios=[
                PaseBeneficiariosPresenter._present_beneficiario(beneficiario)
                for beneficiario in result.beneficiarios
            ],
            compra_id=UUID(result.compra_id) if result.compra_id else None,
            orden_pago_id=(
                UUID(result.orden_pago_id) if result.orden_pago_id else None
            ),
            pase_id=UUID(result.pase_id),
            pase_nombre=result.pase_nombre,
            edicion_nombre=result.edicion_nombre,
            precio_unitario=result.precio_unitario,
            total=result.total,
            moneda=result.moneda,
            causa_operativa=result.causa_operativa,
        )


class PaseBeneficiarioAsignarPresenter:
    """Transformador de la ASIGNACIÓN de un pase a una persona.

    Publica el MISMO wrapper que el listado: la operación devuelve el
    estado actualizado del lote (`RT-PS-05`).
    """

    @staticmethod
    def present_asignacion(result: PaseBeneficiariosResult) -> PaseBeneficiariosOut:
        """Proyecta el lote tras la asignación."""
        return PaseBeneficiariosPresenter.present_beneficiarios(result)


class PaseBeneficiarioPresenter:
    """Transformador de la REVOCACIÓN de un derecho."""

    @staticmethod
    def present_revocacion(
        result: PaseBeneficiarioRevocadoResult,
    ) -> PaseBeneficiarioRevocadoOut:
        """Proyecta el derecho revocado al wrapper HTTP."""
        return PaseBeneficiarioRevocadoOut(
            compra_pase_id=UUID(result.compra_pase_id),
            derecho_id=UUID(result.derecho_id),
            persona_id=UUID(result.persona_id),
            estado=result.estado,
            revocado_en=result.revocado_en,
            ya_revocado=result.ya_revocado,
            motivo=result.motivo,
        )


__all__ = [
    "PaseBeneficiarioAsignarPresenter",
    "PaseBeneficiarioPresenter",
    "PaseBeneficiariosPresenter",
    "PaseCompraDetallePresenter",
]
