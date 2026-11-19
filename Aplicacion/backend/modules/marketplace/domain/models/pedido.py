"""`Pedido` y `PedidoDetalle` — el pedido de marketplace y su detalle.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-MD-1.0.0` (FR-06) ·
        `FREEZE-ED-1.0.0` (FR-02)
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (plan `funcional/03` §1, RN-M03, RN-C01, RN-C02, RN-M07):

    Pedido
      id: UUID               (pk)
      edicion_id: UUID        FK → Edicion
      comprador_id: UUID      FK → Persona (el comprador)
      compra_id: UUID         FK → commerce.Compra (la compra que lo financia)
      estado: PENDIENTE | PAGADO | CANCELADO
      estado_entrega: PENDIENTE | ENTREGADO
      total: Decimal             total CONGELADO por el servidor
      moneda: str                ISO-4217
      token: str                enlace privado de seguimiento (único)
      huella: str               huella de la INTENCIÓN de pedido
      referencia: str           referencia estable de la compra
      created_at, updated_at

    PedidoDetalle
      id: UUID               (pk)
      pedido_id: UUID         FK → Pedido
      tipo_concepto: PRODUCTO
      concepto_id: str
      concepto_nombre: str
      cantidad: int
      precio_unitario: Decimal    precio de catálogo en el momento del pedido
      precio_aplicado: Decimal    precio realmente aplicado (con oferta)

TRES HECHOS SEPARADOS (RN-M07, `QA-M04`, RN-C08):

1. `Pedido.estado` — el ciclo de vida del pedido, propiedad de `marketplace`.
2. `Pedido.estado_entrega` — la entrega, que avanza `DOM-06`. El pago NUNCA
   la avanza: un pedido `PAGADO` con entrega `PENDIENTE` es el estado normal.
3. El estado del PAGO no se guarda aquí: es el hecho comercial de `commerce`
   y el módulo lo proyecta (ver `EstadoPagoPedido`).

El HISTÓRICO NO CAMBIA (RN-M03): el detalle congela el precio unitario y el
precio aplicado en el momento del pedido. Una oferta posterior NO altera ni
el detalle ni el total ya congelados.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel
from modules.marketplace.domain.constants import (
    MONEDA_PEDIDO,
    EstadoEntregaPedido,
    EstadoPedido,
    TipoItemPedido,
)


def validar_total_no_negativo(valor):
    """El total de un pedido nunca es negativo."""
    if valor is None:
        return valor
    if valor < 0:
        raise ValidationError("El total del pedido no puede ser negativo.")
    return valor


class Pedido(BaseModel):
    """Pedido de marketplace: la compra de uno o varios productos."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="pedidos_marketplace",
        verbose_name="Edición",
    )
    comprador = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="pedidos_marketplace",
        verbose_name="Comprador",
    )
    compra = models.ForeignKey(
        "commerce.Compra",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos_marketplace",
        verbose_name="Compra que financia el pedido",
        help_text=(
            "La compra comercial compartida. Es un hecho de `commerce`: el "
            "pedido sólo lo referencia, no lo sustituye (RN-C01)."
        ),
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE,
        verbose_name="Estado del pedido",
    )
    estado_entrega = models.CharField(
        max_length=16,
        choices=EstadoEntregaPedido.choices,
        default=EstadoEntregaPedido.PENDIENTE,
        verbose_name="Estado de la entrega",
        help_text=(
            "Hecho DISTINTO del pago y del estado del pedido. Lo avanza "
            "`DOM-06`; el pago NUNCA lo habilita (RN-M07)."
        ),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[validar_total_no_negativo],
        verbose_name="Total",
        help_text=(
            "Total CONGELADO por el servidor a partir del precio vigente del "
            "catálogo. El cliente no impone un importe (RN-C02)."
        ),
    )
    moneda = models.CharField(
        max_length=3,
        default=MONEDA_PEDIDO,
        verbose_name="Moneda",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token privado de seguimiento",
        help_text=(
            "Enlace privado de consulta del pedido (`/marketplace/pedidos/"
            "{token}`). Es una credencial: nunca se publica en un listado."
        ),
    )
    huella = models.CharField(
        max_length=64,
        verbose_name="Huella de la intención",
        help_text=(
            "Huella de los artículos pedidos. Identifica la INTENCIÓN de "
            "compra: dos peticiones idénticas recoveren el MISMO pedido."
        ),
    )
    referencia = models.CharField(
        max_length=200,
        verbose_name="Referencia de la compra",
        help_text=(
            "Referencia estable de la compra que financia este pedido. La "
            "reutiliza `commerce` para no duplicar la compra (FR-04 I-4)."
        ),
    )

    class Meta:
        db_table = "marketplace_pedido"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="marketplace_pedido_total_no_negativo",
            ),
            # Una persona NO tiene dos pedidos PENDIENTES para la misma
            # intención: reintentar el pedido recupera el existente en vez de
            # duplicarlo (FR-04 I-4, RN-C03, RN-C04).
            models.UniqueConstraint(
                fields=["comprador", "edicion", "huella"],
                condition=models.Q(estado=EstadoPedido.PENDIENTE),
                name="marketplace_pedido_pendiente_unico_por_intencion",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"], name="ix_marketplace_pedido_estado"),
        ]

    def __str__(self) -> str:
        return f"Pedido {self.id} ({self.estado})"


class PedidoDetalle(BaseModel):
    """Una línea del pedido: el producto y el precio CONGELADO."""

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Pedido",
    )
    tipo_concepto = models.CharField(
        max_length=16,
        choices=TipoItemPedido.choices,
        default=TipoItemPedido.PRODUCTO,
        verbose_name="Tipo de concepto",
    )
    concepto_id = models.CharField(
        max_length=64,
        verbose_name="Identificador del concepto",
    )
    concepto_nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del concepto",
        help_text="El nombre en el momento del pedido: el histórico no cambia.",
    )
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario de catálogo",
        help_text=(
            "Precio de catálogo en el momento del pedido. No cambia aunque el "
            "precio vigente cambie después (RN-M03)."
        ),
    )
    precio_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio aplicado",
        help_text=(
            "Precio unitario realmente aplicado (con oferta). Es el que "
            "multiplica la cantidad para el total (RN-C02)."
        ),
    )

    class Meta:
        db_table = "marketplace_pedido_detalle"
        verbose_name = "Detalle del pedido"
        verbose_name_plural = "Detalles del pedido"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="marketplace_pedido_detalle_cantidad_valida",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name="marketplace_pedido_detalle_precio_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_aplicado__gte=0),
                name="marketplace_pedido_detalle_precio_aplicado_no_negativo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.concepto_nombre}"

    @property
    def subtotal(self) -> Decimal:
        """El subtotal de la línea: cantidad × precio aplicado."""
        return (self.precio_aplicado * self.cantidad).quantize(Decimal("0.01"))


__all__ = ["Pedido", "PedidoDetalle", "validar_total_no_negativo"]
