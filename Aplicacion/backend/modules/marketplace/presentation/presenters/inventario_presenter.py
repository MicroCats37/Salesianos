"""Presenters del inventario y de las entregas de marketplace (`DOM-06`).

Contract: `contract/api-wrapper-presenter-contract.md` §3, §8

El presenter es un TRANSFORMADOR PURO: recibe el result object del dominio y
devuelve el wrapper HTTP. No consulta la base de datos, no decide estados y
no construye mensajes de error (sólo el catálogo global lo hace).

**NO EXPONE INTERNOS DEL PROVEEDOR** (FR-01 §4): ni intentos, ni
evidencias, ni referencias técnicas de pago. La bitácora de inventario, en
cambio, SÍ es un hecho público de la tienda: es lo que el operador necesita
para trabajar (`FL-09`).
"""

from modules.marketplace.domain.results.inventario_result import (
    EntregaEntregadaResult,
    EntregaConfirmadaResult,
    EntregaPendienteResult,
    EntregasResult,
    InventarioProductoResult,
    MovimientoInventarioResult,
)
from modules.marketplace.presentation.schemas.inventario_schemas import (
    EntregaEntregadaOut,
    EntregaConfirmadaOut,
    EntregaPendienteOut,
    EntregasOut,
    InventarioProductoOut,
    MovimientoInventarioOut,
)
from modules.marketplace.presentation.schemas.pedido_schemas import PedidoLineaOut


def _present_lineas(lineas) -> list[PedidoLineaOut]:
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


class InventarioPresenter:
    """Presenters del inventario de marketplace (`RT-MK-08`, `RT-MK-09`,
    `RT-MK-12`)."""

    @staticmethod
    def present_movimiento(result: MovimientoInventarioResult) -> MovimientoInventarioOut:
        """Proyecta un movimiento de la bitácora a su wrapper HTTP."""
        return MovimientoInventarioOut(
            id=result.id,
            producto_id=result.producto_id,
            cantidad=result.cantidad,
            tipo=result.tipo,
            motivo=result.motivo,
            referencia=result.referencia,
            actor_id=result.actor_id,
            created_at=result.created_at,
        )

    @staticmethod
    def present_inventario(result: InventarioProductoResult) -> InventarioProductoOut:
        """Proyecta el inventario de un producto a su wrapper HTTP."""
        return InventarioProductoOut(
            producto_id=result.producto_id,
            nombre=result.nombre,
            slug=result.slug,
            stock=result.stock,
            reservado=result.reservado,
            disponible=result.disponible,
            movimientos=[
                InventarioPresenter.present_movimiento(movimiento)
                for movimiento in result.movimientos
            ],
        )

    @staticmethod
    def present_inventario_lista(
        resultados: list[InventarioProductoResult],
    ) -> list[InventarioProductoOut]:
        """Proyecta el inventario de la edición a sus wrappers HTTP."""
        return [InventarioPresenter.present_inventario(resultado) for resultado in resultados]


class EntregaPresenter:
    """Presenters de las entregas de marketplace (`RT-MK-10`, `RT-MK-11`)."""

    @staticmethod
    def present_pendiente(result: EntregaPendienteResult) -> EntregaPendienteOut:
        """Proyecta un pedido pendiente de entrega a su wrapper HTTP."""
        return EntregaPendienteOut(
            pedido_id=result.pedido_id,
            comprador_nombres=result.comprador_nombres,
            comprador_apellidos=result.comprador_apellidos,
            comprador_documento=result.comprador_documento,
            estado=result.estado,
            estado_entrega=result.estado_entrega,
            total=result.total,
            moneda=result.moneda,
            lineas=_present_lineas(result.lineas),
            created_at=result.created_at,
        )

    @staticmethod
    def present_pendientes(
        resultados: list[EntregaPendienteResult],
    ) -> list[EntregaPendienteOut]:
        """Proyecta la cola de entregas a sus wrappers HTTP."""
        return [EntregaPresenter.present_pendiente(resultado) for resultado in resultados]

    @staticmethod
    def present_entregada(result: EntregaEntregadaResult) -> EntregaEntregadaOut:
        """Proyecta un acta de entrega al listado administrativo."""
        return EntregaEntregadaOut(
            pedido_id=result.pedido_id,
            comprador_nombres=result.comprador_nombres,
            comprador_apellidos=result.comprador_apellidos,
            comprador_documento=result.comprador_documento,
            total=result.total,
            moneda=result.moneda,
            lineas=_present_lineas(result.lineas),
            entregada_en=result.entregada_en,
        )

    @staticmethod
    def present_listado(result: EntregasResult) -> EntregasOut:
        """Proyecta las dos colas operativas de recogidas."""
        return EntregasOut(
            pendientes=EntregaPresenter.present_pendientes(result.pendientes),
            entregadas=[
                EntregaPresenter.present_entregada(entrega)
                for entrega in result.entregadas
            ],
        )

    @staticmethod
    def present_confirmada(result: EntregaConfirmadaResult) -> EntregaConfirmadaOut:
        """Proyecta el acta de una entrega a su wrapper HTTP."""
        return EntregaConfirmadaOut(
            pedido_id=result.pedido_id,
            estado_entrega=result.estado_entrega,
            cantidad_total=result.cantidad_total,
            actor_id=result.actor_id,
            entregada_en=result.entregada_en,
            lineas=_present_lineas(result.lineas),
        )


__all__ = ["EntregaPresenter", "InventarioPresenter"]
