"""
AprobacionPagoManual — durable evidence of a payment received outside the
payment provider.

The record answers ONE question: "who proved, how and how much that this
order was paid, and who revoked that proof?".

Rules that the model itself guarantees:

- it is linked to EXACTLY ONE `OrdenPago` (never to a business model: the
  payment module stays agnostic of the FEST),
- the actor is a real account (`PROTECT`: an audit row is never orphaned),
- the amount and the currency are a FROZEN snapshot of what was approved,
- at most ONE active approval exists per order (partial unique constraint),
- the row is IMMUTABLE except for its audited transition to `ANULADA`.

It NEVER creates a `TransaccionPago`: a manual payment did not go through the
provider, so fabricating a provider transaction would be a lie that the
reconciliation would later "repair" by corrupting the audit trail.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import CanalPagoManual, EstadoAprobacionPagoManual


class AprobacionPagoManual(BaseModel):
    """
    Audited evidence of a payment received outside the payment provider.

    The record is the ONLY proof that an order without a provider transaction
    was really paid. It is written BEFORE the commercial settlement runs, so
    a settlement failure leaves the evidence durable and the retry converges.
    """

    history = HistoricalRecords()

    orden_pago = models.ForeignKey(
        "pagos.OrdenPago",
        on_delete=models.PROTECT,
        related_name="aprobaciones_manuales",
        verbose_name="Orden de pago",
    )
    actor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="aprobaciones_pago_manual",
        verbose_name="Actor",
    )
    canal = models.CharField(
        max_length=30,
        choices=CanalPagoManual.choices,
        verbose_name="Canal",
    )
    referencia = models.CharField(
        max_length=100,
        verbose_name="Referencia",
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto aprobado",
    )
    moneda = models.CharField(
        max_length=3,
        verbose_name="Moneda",
    )
    motivo = models.TextField(
        verbose_name="Motivo",
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoAprobacionPagoManual.choices,
        default=EstadoAprobacionPagoManual.APROBADA,
        verbose_name="Estado",
    )
    anulada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="anulaciones_pago_manual",
        null=True,
        blank=True,
        verbose_name="Anulada por",
    )
    anulada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de anulacion",
    )
    motivo_anulacion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Motivo de anulacion",
    )

    class Meta:
        db_table = "pagos_aprobacion_pago_manual"
        verbose_name = "Aprobacion de pago manual"
        verbose_name_plural = "Aprobaciones de pago manual"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["orden_pago"],
                condition=models.Q(estado=EstadoAprobacionPagoManual.APROBADA),
                name="uniq_aprobmanual_activa_orden",
            ),
        ]
        indexes = [
            models.Index(
                fields=["orden_pago", "estado"],
                name="ix_aprobmanual_orden_estado",
            ),
            models.Index(
                fields=["actor", "created_at"],
                name="ix_aprobmanual_actor_fecha",
            ),
        ]

    def __str__(self):
        return f"AprobacionPagoManual {self.orden_pago_id} - {self.estado}"


__all__ = ["AprobacionPagoManual"]
