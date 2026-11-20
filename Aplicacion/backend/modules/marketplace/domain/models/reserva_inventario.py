"""`ReservaInventario` — las existencias APARTADAS por un pedido pendiente.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6
Plan: `RN-M06` · `PD-05` · `funcional/03` §1

**LA ESTRATEGIA ANTI-SOBREVENTA (RN-M06, `PD-05` DECIDIDO).** La reserva es la
UNIDAD que sostiene la garantía: mientras un pedido está `PENDIENTE`, sus
unidades están APARTADAS y no se pueden vender dos veces.

    stock      = unidades físicas que tiene el organizador
    reservado  = unidades apartadas por pedidos pendientes
    disponible = stock - reservado

**PD-05 — DECIDIDO: el stock es POR EDICIÓN.** El inventario vive en el
producto, y el producto pertenece a UNA edición (`Producto.edicion` es
obligatoria y el slug es único por edición). No existe un pool compartido
entre ediciones: el clave del inventario es el producto y, transitivamente,
la edición. Una edición que necesita el mismo artículo lo declara con su
propio producto.

La reserva se CONFIRMA cuando el pago se verifica (las unidades salen del
stock físico) y se LIBERA cuando el pedido se cancela (las unidades vuelven
al catálogo). Las tres cosas —reservar, confirmar, liberar— las decide la
BASE DE DATOS con sentencias condicionales, no la aplicación (F-55 · F-64).
"""

from django.db import models

from core.models import BaseModel

from modules.marketplace.domain.constants import EstadoReservaInventario


class ReservaInventario(BaseModel):
    """Existencias reservadas por un pedido pendiente."""

    producto = models.ForeignKey(
        "marketplace.Producto",
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Producto",
    )
    pedido = models.ForeignKey(
        "marketplace.Pedido",
        on_delete=models.PROTECT,
        related_name="reservas_inventario",
        verbose_name="Pedido",
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad reservada",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoReservaInventario.choices,
        default=EstadoReservaInventario.ACTIVA,
        verbose_name="Estado de la reserva",
    )
    referencia = models.CharField(
        max_length=200,
        verbose_name="Referencia de origen",
        help_text="Referencia del pedido y del producto que originan la reserva.",
    )

    class Meta:
        db_table = "marketplace_reserva_inventario"
        verbose_name = "Reserva de inventario"
        verbose_name_plural = "Reservas de inventario"
        ordering = ["id"]
        constraints = [
            # Un pedido reserva cada producto UNA vez: la cantidad reservada
            # es la SUMA de sus líneas.
            models.UniqueConstraint(
                fields=["pedido", "producto"],
                name="marketplace_reserva_unica_por_pedido_producto",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="marketplace_reserva_cantidad_valida",
            ),
        ]
        indexes = [
            models.Index(
                fields=["producto", "estado"],
                name="ix_mkt_reserva_producto",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.producto_id} · {self.estado}"


__all__ = ["ReservaInventario"]
