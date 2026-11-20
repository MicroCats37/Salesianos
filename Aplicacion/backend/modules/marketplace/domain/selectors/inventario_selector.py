"""Selectores del inventario de marketplace (`DOM-06`).

Contract: `contract/django-app-architecture-contract.md` §4.12

REGLA (F-26): los selectores devuelven LISTAS evaluadas, nunca `QuerySet`.
"""

from modules.marketplace.domain.models import (
    MovimientoInventario,
    Producto,
    ReservaInventario,
)
from modules.marketplace.domain.constants import EstadoReservaInventario


class InventarioSelector:
    """Consultas de lectura sobre el inventario y las entregas."""

    def listar_productos(self, edicion_id) -> list[Producto]:
        """Los productos de una edición, con su inventario."""
        return list(
            Producto.objects.filter(edicion_id=edicion_id).order_by("nombre")
        )

    def listar_movimientos(self, producto_id, limite: int = 50) -> list[MovimientoInventario]:
        """Los últimos movimientos de un producto, del más reciente al más
        antiguo."""
        return list(
            MovimientoInventario.objects.filter(producto_id=producto_id)
            .order_by("-created_at", "-id")
            [:limite]
        )

    def obtener_movimiento(self, movimiento_id) -> MovimientoInventario | None:
        """Un movimiento por su identificador, o `None`."""
        if not movimiento_id:
            return None
        return MovimientoInventario.objects.filter(id=movimiento_id).first()

    def obtener_reservas(self, pedido_id) -> list[ReservaInventario]:
        """Las reservas de un pedido, en su orden canónico."""
        return list(ReservaInventario.objects.filter(pedido_id=pedido_id).order_by("id"))

    def listar_reservas_activas(self, pedido_id) -> list[ReservaInventario]:
        """Las reservas ACTIVAS de un pedido."""
        return list(
            ReservaInventario.objects.filter(
                pedido_id=pedido_id,
                estado=EstadoReservaInventario.ACTIVA,
            ).order_by("id")
        )


__all__ = ["InventarioSelector"]
