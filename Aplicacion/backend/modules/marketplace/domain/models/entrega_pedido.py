"""`EntregaPedido` — el ACTA de entrega de un pedido pagado.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6
Plan: `RN-M07` · `QA-M04` · `FL-08` §5

**PAGADO NO ES ENTREGADO (RN-M07).** El acta de entrega es un hecho
POSTERIOR y SEPARADO del pago:

- el pago habilita el DERECHO (y descuenta el stock, en `DOM-06`);
- la entrega es un ACTA posterior, con su propio actor y su propia hora;
- que el pedido esté pagado NO habilita la entrega.

**IDEMPOTENTE Y REINTENTABLE.** Hay como máximo UN acta por pedido
(restricción única en base de datos): confirmar dos veces la misma entrega
devuelve el MISMO acta, no la duplica. Un reintento del operador es seguro.

**ENTREGA COMPLETA, NO PARCIAL.** La entrega parcial sólo es válida "si se
aprueba ese uso" (`RN-M07`), y esa aprobación NO existe (`PD-03` sigue
ABIERTO y es de A4 + A8 + producto). Este paquete entrega el pedido COMPLETO
y lo deja dicho, en vez de inventar el consumo por unidad.
"""

from django.db import models

from core.models import BaseModel


class EntregaPedido(BaseModel):
    """El acta de entrega de un pedido."""

    pedido = models.ForeignKey(
        "marketplace.Pedido",
        on_delete=models.PROTECT,
        related_name="entregas",
        verbose_name="Pedido",
    )
    actor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="entregas_marketplace",
        verbose_name="Operador",
        help_text="Quién realizó la entrega.",
    )
    referencia = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Referencia de origen",
    )
    cantidad_total = models.PositiveIntegerField(
        verbose_name="Cantidad entregada",
    )
    detalle = models.JSONField(
        default=list,
        verbose_name="Detalle de la entrega",
        help_text=(
            "Snapshot de lo entregado: concepto, nombre y cantidad de cada "
            "línea. Es una foto del momento de la entrega."
        ),
    )

    class Meta:
        db_table = "marketplace_entrega_pedido"
        verbose_name = "Entrega de pedido"
        verbose_name_plural = "Entregas de pedido"
        ordering = ["-created_at", "-id"]
        constraints = [
            # Una entrega por pedido: el reintento del operador NO duplica el
            # acta (entrega idempotente y reintentable).
            models.UniqueConstraint(
                fields=["pedido"],
                name="marketplace_entrega_unica_por_pedido",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_total__gte=1),
                name="marketplace_entrega_cantidad_valida",
            ),
        ]

    def __str__(self) -> str:
        return f"Entrega {self.cantidad_total} · {self.pedido_id}"


__all__ = ["EntregaPedido"]
