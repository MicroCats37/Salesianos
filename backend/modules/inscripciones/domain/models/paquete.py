"""
Paquete and PaqueteDisciplina models for Salesianos FEST.

Paquete: inscription package/product with capacity and pricing.
PaqueteDisciplina: explicit many-to-many relationship between packages and disciplines.
"""

from django.db import models
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords
from decimal import Decimal

from core.models import BaseModel
from modules.inscripciones.domain.constants import ModoDisciplinasPaqueteChoices


class Paquete(BaseModel):
    """
    Inscription package containing multiple disciplines.

    Represents a product offered for sale with capacity and pricing.
    """

    history = HistoricalRecords()

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del paquete"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    cantidad_maxima_participantes = models.PositiveIntegerField(
        verbose_name="Cantidad máxima de participantes",
        help_text="Límite total de personas únicas en el paquete"
    )
    precio_regular = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio regular"
    )
    precio_promocional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio promocional"
    )
    valido_desde = models.DateField(
        verbose_name="Válido desde"
    )
    valido_hasta = models.DateField(
        verbose_name="Válido hasta"
    )
    esta_activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?"
    )
    modo_disciplinas = models.CharField(
        max_length=20,
        choices=ModoDisciplinasPaqueteChoices.choices,
        default=ModoDisciplinasPaqueteChoices.ELEGIBLE,
        verbose_name="Modo de disciplinas",
        help_text="FIJO: disciplinas predefinidas. ELEGIBLE: usuario elige entre las permitidas."
    )
    cantidad_disciplinas_requeridas = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de disciplinas requeridas",
        help_text="Número de disciplinas que el usuario debe seleccionar (para modo ELEGIBLE)."
    )

    class Meta:
        verbose_name = "Paquete"
        verbose_name_plural = "Paquetes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class PaqueteDisciplina(BaseModel):
    """
    Explicit through table linking Paquete to Disciplina.

    Defines which disciplines are included in a package.
    """

    history = HistoricalRecords()

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.CASCADE,
        related_name="paquete_disciplinas",
        verbose_name="Paquete"
    )
    disciplina = models.ForeignKey(
        "inscripciones.Disciplina",
        on_delete=models.CASCADE,
        related_name="paquete_disciplinas",
        verbose_name="Disciplina"
    )

    class Meta:
        verbose_name = "Disciplina de paquete"
        verbose_name_plural = "Disciplinas de paquete"
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "disciplina"],
                name="unique_paquete_disciplina"
            )
        ]

    def __str__(self):
        return f"{self.paquete.nombre} - {self.disciplina.nombre}"
