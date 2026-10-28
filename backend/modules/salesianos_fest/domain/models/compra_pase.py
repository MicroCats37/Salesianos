"""
CompraPase — commercial line of a party-pass purchase.

Mirrors `CompraInscripcion` (the sports composition) but for the independent
party-pass catalogue: a purchase of N passes. It NEVER creates a sports
object — there is no `Inscripcion`, no `CompraInscripcion`, no `AsignacionCupo`
and no `Participacion` behind a pass purchase.

Attributes:
    compra: OneToOne link to the generic commerce.Compra.
    pase: FK to the purchased Pase.
    evento: FK to the Evento — denormalised scope. `Compra` has no event of
        its own and the administrative queries scope by event.
    cantidad: Number of passes purchased (NOT sports cupos).
    precio_unitario: Frozen unit price at purchase time.
    total: Frozen total = cantidad * precio_unitario.

There is NO `estado` column: the commercial state lives in `Compra.estado`
(single source of truth). The pass purchase is settled by the generic
payment machinery and never enters the sports allocator.
"""
from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento

from .pase import Pase


class CompraPase(BaseModel):
    """
    Links a generic commerce.Compra to a party pass with purchase specifics.

    One CompraPase per commercial purchase: a second purchase of the same
    pass creates a NEW batch (new Compra + new CompraPase).
    """

    compra = models.OneToOneField(
        "commerce.Compra",
        on_delete=models.PROTECT,
        related_name="compra_pase",
        verbose_name="Compra generica",
    )
    pase = models.ForeignKey(
        Pase,
        on_delete=models.PROTECT,
        related_name="compras_pase",
        verbose_name="Pase",
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="compras_pase",
        verbose_name="Evento",
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad de pases",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario snapshot",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total snapshot",
    )

    class Meta:
        db_table = "salesianos_fest_compra_pase"
        verbose_name = "Compra Pase"
        verbose_name_plural = "Compras Pase"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["compra"],
                name="unique_compra_por_pase",
            ),
        ]
        indexes = [
            models.Index(
                fields=["evento"],
                name="idx_compra_pase_evento",
            ),
            models.Index(
                fields=["pase", "created_at"],
                name="idx_compra_pase_pase",
            ),
        ]

    def __str__(self) -> str:
        return f"CompraPase - {self.pase} - {self.cantidad} - {self.compra.estado}"
