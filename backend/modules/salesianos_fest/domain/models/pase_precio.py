"""
PasePrecio — precios por etapa de un pase de fiesta.
"""
from django.db import models
from django.db.models import Q

from core.models import BaseModel

from .pase import Pase
from ..constants import EtapaChoices


class PasePrecio(BaseModel):
    """
    Precio de un pase según la etapa de venta.

    Réplica exacta de `PaquetePrecio` (misma forma y misma restricción
    parcial) para que el calendario de etapas y la regla de precio vigente
    sean idénticos en ambos catálogos.

    Attributes:
        pase: Pase al que pertenece el precio.
        etapa: PREVENTA o REGULAR.
        precio_unitario: Precio en soles.
        vigente_desde: Fecha desde la que aplica este precio.
        vigente_hasta: Fecha hasta la que aplica (null = sin límite).
        activo: Indica si este precio está vigente.
    """

    pase = models.ForeignKey(
        Pase,
        on_delete=models.PROTECT,
        related_name="precios",
        verbose_name="Pase",
    )
    etapa = models.CharField(
        max_length=10,
        choices=EtapaChoices.choices,
        verbose_name="Etapa",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario (S/)",
    )
    vigente_desde = models.DateField(
        verbose_name="Vigente desde",
    )
    vigente_hasta = models.DateField(
        blank=True,
        null=True,
        verbose_name="Vigente hasta",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?",
    )

    class Meta:
        db_table = "pases_precios"
        verbose_name = "Precio de pase"
        verbose_name_plural = "Precios de pases"
        ordering = ["pase", "etapa"]
        constraints = [
            models.UniqueConstraint(
                fields=["pase", "etapa"],
                condition=Q(activo=True),
                name="unique_pase_precio_vigente_etapa",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pase.nombre} - {self.etapa} - S/{self.precio_unitario}"
