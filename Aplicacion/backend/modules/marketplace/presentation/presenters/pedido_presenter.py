"""Presenters del pedido de marketplace (`DOM-05`).

Contract: `contract/api-wrapper-presenter-contract.md` §3, §8

El presenter es un TRANSFORMADOR PURO: recibe el result object del dominio y
devuelve el wrapper HTTP. No consulta la base de datos, no decide estados y
no construye mensajes de error (sólo el catálogo global lo hace).

**Lo que el presenter NO expone (FR-01 §4):** ninguna referencia técnica del
proveedor, ningún intento, ninguna evidencia, ninguna firma, ningún
identificador interno de la compra ni metadatos del pago. Lo que sí expone
son los TRES estados del pedido (pedido, pago y entrega) y la siguiente
acción SEGURA que el comprador puede realizar.
"""

from modules.marketplace.domain.results.pedido_result import (
    PedidoCreadoResult,
    PedidoLineaResult,
    PedidoSeguimientoResult,
)
from modules.marketplace.presentation.schemas.pedido_schemas import (
    PedidoCreadoOut,
    PedidoLineaOut,
    PedidoSeguimientoOut,
)


def _present_lineas(lineas: list[PedidoLineaResult]) -> list[PedidoLineaOut]:
    """Proyecta las líneas del pedido a sus wrappers HTTP."""
    return [
        PedidoLineaOut(
            tipo_concepto=linea.tipo_concepto,
            concepto_id=linea.concepto_id,
            concepto_nombre=linea.concepto_nombre,
            cantidad=linea.cantidad,
            precio_unitario=linea.precio_unitario,
            precio_aplicado=linea.precio_aplicado,
            subtotal=linea.subtotal,
        )
        for linea in lineas
    ]


class PedidoPresenter:
    """Presenter de `RT-CM-03` (alta del pedido)."""

    @staticmethod
    def present(result: PedidoCreadoResult) -> PedidoCreadoOut:
        """Proyecta el result del pedido al wrapper HTTP."""
        return PedidoCreadoOut(
            id=result.id,
            token=result.token,
            estado=result.estado,
            estado_pago=result.estado_pago,
            estado_entrega=result.estado_entrega,
            total=result.total,
            moneda=result.moneda,
            lineas=_present_lineas(result.lineas),
            orden_pago_id=result.orden_pago_id,
            siguientes_acciones=list(result.siguientes_acciones),
            recuperado=result.recuperado,
            created_at=result.created_at,
        )


class PedidoSeguimientoPresenter:
    """Presenter de `RT-MK-04` (seguimiento del pedido)."""

    @staticmethod
    def present(result: PedidoSeguimientoResult) -> PedidoSeguimientoOut:
        """Proyecta el result del seguimiento al wrapper HTTP."""
        return PedidoSeguimientoOut(
            id=result.id,
            estado=result.estado,
            estado_pago=result.estado_pago,
            estado_entrega=result.estado_entrega,
            total=result.total,
            moneda=result.moneda,
            lineas=_present_lineas(result.lineas),
            orden_pago_id=result.orden_pago_id,
            siguientes_acciones=list(result.siguientes_acciones),
            created_at=result.created_at,
        )


__all__ = ["PedidoPresenter", "PedidoSeguimientoPresenter"]
