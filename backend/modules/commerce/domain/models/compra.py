"""
Compra — generic commercial purchase aggregate.

Purely generic: no FK to any business domain model (salesianos_fest, store, etc.).
Owns buyer/responsible, commercial status, total snapshot, description, and
external reference.

Composition:
- pagos.OrdenPago: OneToOne (each Compra has exactly one payment order)
- Future store: store.CompraTiendaItem → Compra via FK
- FEST: salesianos_fest.CompraInscripcion → Compra via OneToOne

Anti-patterns explicitly rejected:
- entity_type / entity_id discriminator
- GenericForeignKey
- Django model inheritance for variants
"""
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import EstadoCompraChoices


class Compra(BaseModel):
    """
    Generic commercial purchase aggregate.

    Attributes:
        responsable: Person who makes the purchase (nullable for future
            unauthenticated store purchases).
        descripcion: Generic description for display/auditing.
        referencia_externa: Business reference (e.g. "FEST Purchase", "Store Order").
        total: Frozen total amount snapshot.
        estado: Commercial state (PENDIENTE/PAGADA/CANCELADA).
        orden_pago: The associated payment order (OneToOne).
    """

    history = HistoricalRecords()

    responsable = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="compras",
        verbose_name="Responsable",
        null=True,
        blank=True,
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Descripcion",
    )
    referencia_externa = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Referencia externa",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total snapshot",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoCompraChoices.choices,
        default=EstadoCompraChoices.PENDIENTE,
        verbose_name="Estado",
    )
    orden_pago = models.OneToOneField(
        "pagos.OrdenPago",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Orden de pago",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "commerce_compra"
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Compra {self.id} - {self.estado}"
