"""`Compra` — el agregado comercial compartido.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (FR-04 §1.1, literal):

    Compra
      id: UUID            (pk)
      persona_id: UUID     FK → Persona — el comprador. Obligatoria
      origen: INSCRIPCION | PASE | MARKETPLACE
      estado: PENDIENTE | PAGADA | CANCELADA
      total: Decimal      congelado en el momento de la compra
      moneda: ISO-4217    ("PEN"). Prohibido `float` para montos
      lineas_snapshot:    snapshot inmutable de lo comprado
      orden_pago_id:      FK → OrdenPago, nullable mientras `estado = PENDIENTE`
      referencia:         referencia de la intención de compra
      creada_en, actualizada_en: timestamps

Prohibiciones del agregado (FR-04 §1.1):

1. **Prohibido** un carrito conjunto: no existe una compra que mezcle
   orígenes (`DEC-10`, `RN-C01`).
2. **Prohibido** una compra sin `origen`.
3. **Prohibido** recalcular `total` o `lineas_snapshot` después de creada. Una
   corrección comercial es una compra nueva con su propio rastro.

Sobre la relación con `pagos.OrdenPago`: la FK la posee `Compra.orden_pago`
(OneToOne, nullable, `related_name="+"`). Así la dirección de dependencias es
`commerce -> pagos` y el módulo de pago nunca importa este módulo: pregunta
por el estado comercial de la compra a través del **port**
`IEstadoCompraOrdenPagoService`.
"""

from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from modules.commerce.domain.constants import EstadoCompra, OrigenCompra


def validar_total_no_negativo(valor):
    """El total de una compra nunca es negativo."""
    if valor is None:
        return valor
    if valor < 0:
        raise ValidationError("El total de la compra no puede ser negativo.")
    return valor


class Compra(BaseModel):
    """Compra comercial: el agregado compartido por los tres dominios."""

    history = HistoricalRecords()

    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="compras",
        verbose_name="Comprador",
        help_text=(
            "La persona que compra. Una compra SIEMPRE tiene comprador: una "
            "cuenta técnica sin persona no puede comprar."
        ),
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenCompra.choices,
        verbose_name="Origen",
        help_text=(
            "Dominio de origen de la compra. Tres valores cerrados, uno por "
            "dominio. No existe una compra genérica sin origen."
        ),
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoCompra.choices,
        default=EstadoCompra.PENDIENTE,
        verbose_name="Estado",
        help_text=(
            "Hecho COMERCIAL. Distinto del estado de la orden de pago y del "
            "estado del intento (FR-04 §1.3)."
        ),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[validar_total_no_negativo],
        verbose_name="Total",
        help_text=(
            "Monto congelado en el momento de la compra. Lo calcula el "
            "servidor a partir de las líneas: el cliente no impone un importe."
        ),
    )
    moneda = models.CharField(
        max_length=3,
        default="PEN",
        verbose_name="Moneda",
        help_text="Código ISO-4217 del total. Prohibido `float` para montos.",
    )
    lineas_snapshot = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Líneas de la compra",
        help_text=(
            "Snapshot inmutable de lo comprado (concepto, cantidad, precio "
            "unitario y precio aplicado). No cambia aunque el precio vigente "
            "cambie después (`RN-M03`)."
        ),
    )
    orden_pago = models.OneToOneField(
        "pagos.OrdenPago",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Orden de pago",
        null=True,
        blank=True,
        help_text=(
            "La orden de pago que financia la compra. Nula mientras la compra "
            "está pendiente."
        ),
    )
    referencia = models.CharField(
        max_length=200,
        verbose_name="Referencia de la intención",
        help_text=(
            "Referencia de la intención de compra. Es lo que permite REUSAR "
            "una compra pendiente en vez de duplicarla (FR-04 I-4)."
        ),
    )

    class Meta:
        db_table = "commerce_compra"
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="compra_total_no_negativo",
            ),
            # Una persona no tiene dos compras PENDIENTES para la misma
            # intención: reabrir el checkout reutiliza la existente en vez de
            # duplicarla (FR-04 I-4). Una vez pagada o cancelada, la misma
            # referencia puede abrir una compra nueva.
            models.UniqueConstraint(
                fields=["persona", "referencia"],
                condition=models.Q(estado=EstadoCompra.PENDIENTE),
                name="compra_pendiente_unica_por_comprador",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"], name="ix_compra_estado"),
            models.Index(fields=["origen"], name="ix_compra_origen"),
        ]

    def __str__(self) -> str:
        return f"Compra {self.id} ({self.origen}) - {self.estado}"

    # ── Conveniencias triviales (sin lógica de negocio) ────────────────────

    @property
    def esta_pagada(self) -> bool:
        """Si la compra consta como pagada."""
        return self.estado == EstadoCompra.PAGADA

    @property
    def esta_cancelada(self) -> bool:
        """Si la compra está cancelada."""
        return self.estado == EstadoCompra.CANCELADA
