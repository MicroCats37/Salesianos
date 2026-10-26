"""
CompraSelector — query interface for Compra.

Now operates on commerce.Compra + CompraInscripcion composition.
"""
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra


class CompraSelector:
    """Query interface for Compra (commerce.Compra + CompraInscripcion)."""

    def obtener_por_id(self, compra_id: str) -> Compra | None:
        """Get a commerce.Compra by its ID with select_related."""
        return (
            Compra.objects
            .select_related("orden_pago", "compra_inscripcion", "compra_inscripcion__inscripcion__responsable")
            .filter(id=compra_id)
            .first()
        )

    def obtener_por_orden_pago(self, orden_pago_id: str) -> Compra | None:
        """Get a commerce.Compra by its OrdenPago ID."""
        return (
            Compra.objects
            .select_related("orden_pago", "compra_inscripcion")
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )

    def listar_por_inscripcion(self, inscripcion_id: str) -> list[Compra]:
        """List all compras for an inscripcion via CompraInscripcion."""
        return list(
            Compra.objects
            .select_related("orden_pago", "compra_inscripcion")
            .filter(compra_inscripcion__inscripcion_id=inscripcion_id)
            .order_by("-created_at")
        )

    def listar_pendientes_con_orden_pago(
        self,
        orden_pago_id: str | None = None,
    ) -> list[Compra]:
        """
        List the purchases that are still PENDIENTE and linked to an order.

        These are the commercial side of the paid/pending gap: the order was
        paid but its purchase was never settled.
        """
        compras = Compra.objects.filter(
            estado=EstadoCompraChoices.PENDIENTE,
            orden_pago__isnull=False,
        )
        if orden_pago_id:
            compras = compras.filter(orden_pago_id=orden_pago_id)
        return list(
            compras
            .select_related("orden_pago")
            .order_by("created_at")
        )
