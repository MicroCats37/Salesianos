"""
PaqueteBeneficio — beneficios incluidos en un paquete.
"""
from django.db import models

from core.models import BaseModel
from .paquete import Paquete
from ..constants import TipoBeneficioChoices, AlcanceBeneficioChoices, ModoCalculoBeneficioChoices


class PaqueteBeneficio(BaseModel):
    """
    Define los beneficios incluidos en un paquete.

    Attributes:
        paquete: Paquete al que pertenece el beneficio.
        tipo: FIESTA, BOX o CERVEZA.
        cantidad: Cantidad del beneficio.
        alcance: INDIVIDUAL o GRUPAL.
        modo_calculo: POR_CUPO o FIJO_INICIAL.
    """

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        related_name="beneficios",
        verbose_name="Paquete",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoBeneficioChoices.choices,
        verbose_name="Tipo de beneficio",
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad",
    )
    alcance = models.CharField(
        max_length=20,
        choices=AlcanceBeneficioChoices.choices,
        verbose_name="Alcance",
    )
    modo_calculo = models.CharField(
        max_length=20,
        choices=ModoCalculoBeneficioChoices.choices,
        verbose_name="Modo de cálculo",
    )

    class Meta:
        db_table = "paquetes_beneficios"
        verbose_name = "Beneficio de paquete"
        verbose_name_plural = "Beneficios de paquetes"
        ordering = ["paquete", "tipo"]
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "tipo"],
                name="unique_paquete_beneficio_tipo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.paquete.nombre} - {self.tipo}"
