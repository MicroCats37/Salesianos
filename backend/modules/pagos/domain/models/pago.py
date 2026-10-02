"""
IzipayTransaccion model — represents a single Izipay gateway transaction attempt.

Each row is one payment attempt. Multiple attempts per inscription are allowed.
transaction_id is the idempotency key (unique per gateway call).
"""
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import IzipayStatus


class IzipayTransaccion(BaseModel):
    """
    Single Izipay gateway transaction attempt.

    provider=IZIPAY is fixed (not the payment method).
    Multiple attempts per inscripcion are allowed.
    transaction_id is the idempotency key.
    """

    history = HistoricalRecords()

    PROVEEDOR_DEFAULT = "IZIPAY"
    MONEDA_DEFAULT = "PEN"

    inscripcion = models.ForeignKey(
        "inscripciones.Inscripcion",
        on_delete=models.PROTECT,
        related_name="transacciones_izipay",
        verbose_name="Inscripcion"
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
        verbose_name = "Transaccion Izipay"
        verbose_name_plural = "Transacciones Izipay"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["inscripcion", "status"], name="ix_izipay_insc_status"),
            models.Index(fields=["inscripcion", "created_at"], name="ix_izipay_insc_created"),
        ]

    def __str__(self):
        return f"Izipay {self.transaction_id} - {self.status}"
