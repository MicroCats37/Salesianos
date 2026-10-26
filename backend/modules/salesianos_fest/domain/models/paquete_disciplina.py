"""
PaqueteDisciplina — disciplinas vinculadas a un paquete.
"""
from django.db import models

from core.models import BaseModel
from .paquete import Paquete
from .disciplina import Disciplina


class PaqueteDisciplina(BaseModel):
    """
    Vincula disciplinas a un paquete.

    Attributes:
        paquete: Paquete al que pertenece la disciplina.
        disciplina: Disciplina vinculada.
    """

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        related_name="paquete_disciplinas",
        verbose_name="Paquete",
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.PROTECT,
        related_name="paquete_disciplinas",
        verbose_name="Disciplina",
    )

    class Meta:
        db_table = "paquetes_disciplinas"
        verbose_name = "Disciplina de paquete"
        verbose_name_plural = "Disciplinas de paquetes"
        ordering = ["paquete", "disciplina"]
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "disciplina"],
                name="unique_paquete_disciplina",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.paquete.nombre} - {self.disciplina.nombre}"
