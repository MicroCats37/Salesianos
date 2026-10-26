"""
OrdenPago — generic payment order, agnostic of business domain.

Each OrdenPago represents a payment obligation. It is created when a Compra
is initiated and is independent of the business context (inscripcion, evento, etc.).

The OneToOne relationship is owned by commerce.Compra, so pagos never imports
or points to a business or commerce model.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import IzipayStatus, OrdenPagoStatus


class OrdenPago(BaseModel):
    """
    Generic payment order — a commitment to pay a certain amount.

    Created when a commercial purchase (Compra) is initiated.
    The Izipay transaction(s) that settle it reference this order.

    Not coupled to any business domain model — pagos is the business-agnostic
    payment layer. Its business context is represented only by display/audit
    snapshots supplied when the order is created.

    Fields descripcion and referencia_externa are display/audit snapshots
    set by the business module when creating the orden.
    """

    history = HistoricalRecords()

    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numero de orden"
    )
    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto total"
    )
    moneda = models.CharField(
        max_length=3,
        default="PEN",
        verbose_name="Moneda"
    )
    estado = models.CharField(
        max_length=15,
        choices=OrdenPagoStatus.choices,
        default=OrdenPagoStatus.PENDIENTE,
        verbose_name="Estado"
    )
    pagada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de expiracion"
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Descripcion de la orden",
    )
    referencia_externa = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Referencia externa del negocio",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadatos de contexto",
    )

    class Meta:
        verbose_name = "Orden de pago"
        verbose_name_plural = "Ordenes de pago"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OrdenPago {self.numero} - {self.estado}"


class TransaccionPago(BaseModel):
    """
    Single Izipay gateway transaction attempt linked to an OrdenPago.

    Replaces IzipayTransaccion — removes inscripcion FK and adds orden_pago FK.
    Multiple attempts can be made per order (retry on failure).
    """

    history = HistoricalRecords()

    PROVEEDOR_DEFAULT = "IZIPAY"
    MONEDA_DEFAULT = "PEN"

    orden_pago = models.ForeignKey(
        OrdenPago,
        on_delete=models.PROTECT,
        related_name="transacciones",
        verbose_name="Orden de pago"
    )
    proveedor = models.CharField(
        max_length=20,
        default=PROVEEDOR_DEFAULT,
        editable=False,
        verbose_name="Proveedor"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Transaction ID Izipay"
    )
    order_number = models.CharField(
        max_length=100,
        verbose_name="Numero de orden"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto"
    )
    currency = models.CharField(
        max_length=3,
        default=MONEDA_DEFAULT,
        verbose_name="Moneda"
    )
    status = models.CharField(
        max_length=20,
        choices=IzipayStatus.choices,
        default=IzipayStatus.PENDIENTE,
        verbose_name="Estado"
    )
    response_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Codigo de respuesta"
    )
    response_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensaje de respuesta"
    )
    metodo_pago = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Metodo de pago"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadatos"
    )

    class Meta:
        verbose_name = "Transaccion de pago"
        verbose_name_plural = "Transacciones de pago"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["orden_pago", "status"], name="ix_transpago_orden_status"),
            models.Index(fields=["orden_pago", "created_at"], name="ix_transpago_orden_created"),
        ]

    def __str__(self):
        return f"Transaccion {self.transaction_id} - {self.status}"


# Backwards compatibility alias
IzipayTransaccion = TransaccionPago
