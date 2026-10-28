"""
CompraPaseSelector — queries for the pass purchase (Compra + CompraPase + OrdenPago).

Read-only: it never writes and never transforms to the HTTP layer.
"""
from typing import Optional

from injector import inject

from modules.pagos.domain.constants import OrigenPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.salesianos_fest.domain.models import CompraPase
from modules.salesianos_fest.domain.results.pase_results import PaseCompraDetalleResult


class CompraPaseSelector:
    """Query interface for the pass purchase."""

    @inject
    def __init__(self, evidencia_pago: EvidenciaPagoService):
        self.evidencia_pago = evidencia_pago

    def obtener_detalle(self, compra_id: str) -> Optional[PaseCompraDetalleResult]:
        """
        Return the detail of a pass purchase, or None when there is none.

        A purchase that is not a pass purchase (a sports purchase) has no
        detail here: it is simply not a pass purchase.

        `origen_pago` is DERIVED from the payment evidence of the order (a
        correlated successful provider transaction or an active manual
        approval) — it is never a field anybody can type.
        """
        linea = (
            CompraPase.objects
            .filter(compra_id=compra_id)
            .select_related(
                "compra",
                "compra__orden_pago",
                "compra__responsable",
                "pase",
            )
            .first()
        )
        if linea is None:
            return None

        compra = linea.compra
        orden_pago = compra.orden_pago

        # Los conteos de beneficiarios los calcula el flujo que lee la compra
        # (los slots son inmutables: un slot revocado sigue consumido). Aquí
        # se deja el valor neutro de un lote sin derechos asignados.
        beneficiarios_asignados = 0
        beneficiarios_pendientes = linea.cantidad

        return PaseCompraDetalleResult(
            compra_id=str(compra.id),
            compra_pase_id=str(linea.id),
            orden_pago_id=str(orden_pago.id) if orden_pago else "",
            numero_orden=orden_pago.numero if orden_pago else "",
            pase_id=str(linea.pase_id),
            pase_nombre=linea.pase.nombre,
            cantidad=linea.cantidad,
            precio_unitario=linea.precio_unitario,
            total=linea.total,
            estado_compra=compra.estado,
            estado_orden=orden_pago.estado if orden_pago else "",
            moneda=orden_pago.moneda if orden_pago else "",
            origen_pago=self._derivar_origen(orden_pago),
            created_at=compra.created_at,
            responsable_id=str(compra.responsable_id) if compra.responsable_id else "",
            beneficiarios_asignados=beneficiarios_asignados,
            beneficiarios_pendientes=beneficiarios_pendientes,
        )

    def _derivar_origen(self, orden_pago) -> str:
        """
        Return the origin of the payment evidence of the order.

        `IZIPAY`, `MANUAL` or `SIN_PAGO`. The origin is derived from the
        evidence: an order without evidence has NO origin yet.
        """
        if orden_pago is None:
            return OrigenPago.SIN_PAGO
        return self.evidencia_pago.origen_pago(orden_pago)
