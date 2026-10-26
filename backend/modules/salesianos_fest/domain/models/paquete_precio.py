"""
PaquetePrecio — precios por etapa de un paquete.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Q

from core.models import BaseModel
from .paquete import Paquete
from ..constants import EtapaChoices


class PaquetePrecio(BaseModel):
    """
    Define el precio de un paquete según la etapa de venta.

    Attributes:
        paquete: Paquete al que pertenece el precio.
        etapa: PREVENTA o REGULAR.
        precio_unitario: Precio en soles.
        vigente_desde: Fecha desde la que aplica este precio.
        vigente_hasta: Fecha hasta la que aplica (null = sin límite).
        activo: Indica si este precio está vigente.
    """

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        related_name="precios",
        verbose_name="Paquete",
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
        db_table = "paquetes_precios"
        verbose_name = "Precio de paquete"
        verbose_name_plural = "Precios de paquetes"
        ordering = ["paquete", "etapa"]
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "etapa"],
                condition=Q(activo=True),
                name="unique_paquete_precio_vigente_etapa",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.paquete.nombre} - {self.etapa} - S/{self.precio_unitario}"
