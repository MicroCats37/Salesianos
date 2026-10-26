"""
CompraInscripcion — links a generic Compra to a FEST Inscripcion with purchase details.

Composition pattern: salesianos_fest composes commerce.Compra via CompraInscripcion.

Attributes:
    compra: OneToOne link to the generic commerce.Compra.
    inscripcion: FK to the FEST Inscripcion.
    tipo: INICIAL (first purchase) or AMPLIACION (subsequent expansion).
    cantidad: Number of cupos purchased.
    precio_unitario: Frozen unit price at purchase time.
    total: Frozen total = cantidad * precio_unitario.

Constraints:
    - UniqueConstraint partial: (inscripcion, tipo=INICIAL) — one initial purchase per inscription.
    - cantidad for AMPLIACION does not enforce minimum (minimum only applies to INICIAL).

Anti-patterns explicitly rejected:
    - entity_type / entity_id discriminator (replaced by FK composition)
    - GenericForeignKey
    - Django model inheritance for variants
"""
from django.db import models

from core.models import BaseModel
from .inscripcion import Inscripcion
from ..constants import TipoCompraChoices


class CompraInscripcion(BaseModel):
    """
    Links a generic commerce.Compra to a FEST Inscripcion with purchase specifics.

    One CompraInscripcion per commercial purchase. An Inscripcion can have
    one INICIAL CompraInscripcion and N AMPLIACION CompraInscripcion.
    """

    compra = models.OneToOneField(
        "commerce.Compra",
        on_delete=models.PROTECT,
        related_name="compra_inscripcion",
        verbose_name="Compra generica",
    )
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.PROTECT,
        related_name="compras_inscripcion",
        verbose_name="Inscripcion",
    )
    tipo = models.CharField(
        max_length=15,
        choices=TipoCompraChoices.choices,
        verbose_name="Tipo de compra",
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad de cupos",
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
        db_table = "salesianos_fest_compra_inscripcion"
        verbose_name = "Compra Inscripcion"
        verbose_name_plural = "Compras Inscripcion"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion", "tipo"],
                condition=models.Q(tipo=TipoCompraChoices.INICIAL),
                name="unique_inicial_por_inscripcion",
            ),
        ]

    def __str__(self) -> str:
        return f"CompraInscripcion {self.tipo} - {self.inscripcion} - {self.compra.estado}"
