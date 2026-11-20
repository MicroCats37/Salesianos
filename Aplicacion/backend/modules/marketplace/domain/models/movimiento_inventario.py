"""`MovimientoInventario` — la BITÁCORA del inventario.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6
Plan: `RN-M04` · `RN-M05` · `funcional/03` §1, §5

Todo movimiento de inventario declara:

    producto · signo/cantidad · motivo · referencia de origen · actor

La referencia de origen es **ÚNICA**: un movimiento de venta con la misma
referencia NO se registra dos veces (`FR-04` I-3). Por eso un webhook
repetido no descuenta el stock dos veces (`RN-M06`).

**INMUTABLE.** El movimiento no se edita ni se borra: una corrección es un
movimiento COMPENSATORIO que apunta al original (`funcional/03` §5: "un
movimiento de inventario no se borra para ocultar operaciones; reversas con
movimiento compensatorio si procede").
"""

from django.db import models

from core.models import BaseModel

from modules.marketplace.domain.constants import TipoMovimientoInventario
from modules.marketplace.domain.exceptions import MovimientoInmutableError


class MovimientoInventario(BaseModel):
    """Un movimiento de inventario: la bitácora INMUTABLE."""

    producto = models.ForeignKey(
        "marketplace.Producto",
        on_delete=models.PROTECT,
        related_name="movimientos",
        verbose_name="Producto",
    )
    cantidad = models.IntegerField(
        verbose_name="Cantidad con signo",
        help_text=(
            "Signo y cantidad: positiva es una ENTRADA, negativa es una SALIDA "
            "(RN-M04)."
        ),
    )
    tipo = models.CharField(
        max_length=24,
        choices=TipoMovimientoInventario.choices,
        verbose_name="Naturaleza del movimiento",
    )
    motivo = models.CharField(
        max_length=200,
        verbose_name="Motivo",
        help_text="Motivo del movimiento: es obligatorio en las salidas.",
    )
    referencia = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Referencia de origen",
        help_text=(
            "Referencia que identifica el ORIGEN del movimiento y lo hace "
            "ÚNICO: una venta con la misma referencia NO se registra dos veces "
            "(FR-04 I-3)."
        ),
    )
    actor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
        verbose_name="Actor",
        help_text="Quién lo registró. Es obligatorio en los movimientos manuales.",
    )
    compensatorio = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversiones",
        verbose_name="Movimiento compensatorio",
        help_text="Movimiento original que este compensa, si lo compensa.",
    )

    class Meta:
        db_table = "marketplace_movimiento_inventario"
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0) | models.Q(cantidad__lt=0),
                name="marketplace_movimiento_cantidad_no_cero",
            ),
        ]
        indexes = [
            models.Index(
                fields=["producto", "-created_at"],
                name="ix_mkt_movimiento_producto",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.cantidad:+d} · {self.producto_id}"

    # ── Inmutabilidad (RN-M04) ───────────────────────────────────────────────

    def save(self, *args, **kwargs):
        """El movimiento se INSERTA, nunca se edita.

        La bitácora es la prueba de lo que pasó: un movimiento corregido es un
        movimiento nuevo que compensa al anterior, no una edición.
        """
        if not self._state.adding:
            raise MovimientoInmutableError()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Un movimiento no se borra: se compensa con otro (RN-M04)."""
        raise MovimientoInmutableError()


__all__ = ["MovimientoInventario"]
