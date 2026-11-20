"""`Producto` — el artículo del catálogo de la tienda.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (plan `funcional/03` §1, RN-M02):

    Producto
      id: UUID             (pk)
      edicion_id: UUID      FK → Edicion
      categoria_id: UUID     FK → CategoriaProducto (opcional)
      nombre: str
      slug: str            único por edición
      descripcion: str
      precio: Decimal            precio normal
      precio_oferta: Decimal     precio de oferta (opcional)
      oferta_inicia: datetime    inicio de la oferta (opcional)
      oferta_termina: datetime   fin de la oferta (opcional)
      estado: ACTIVO | INACTIVO
      created_at, updated_at

El precio es `Decimal`: el dinero nunca es `float` en el dominio. La
efectividad de la oferta (qué precio rige y si la oferta está vigente) la
calcula el DOMINIO, nunca el cliente: `precio_efectivo` y `oferta_activa`
viajan en el result object.

Este modelo declara las EXISTENCIAS (`stock` y `reservado`) desde DOM-06: el
catálogo no inventa disponibilidad, la declara. El inventario —la bitácora de
movimientos, las reservas y las entregas— vive en `MovimientoInventario`,
`ReservaInventario` y `EntregaPedido`.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone

from core.models import BaseModel

from modules.marketplace.domain.constants import EstadoProducto


class Producto(BaseModel):
    """Producto del catálogo, acotado a una edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Edición",
    )
    categoria = models.ForeignKey(
        "marketplace.CategoriaProducto",
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True,
        verbose_name="Categoría",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del producto",
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name="Identificador del producto",
        help_text="Identificador único dentro de la edición.",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio",
    )
    precio_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio de oferta",
    )
    oferta_inicia = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio de la oferta",
    )
    oferta_termina = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin de la oferta",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoProducto.choices,
        default=EstadoProducto.ACTIVO,
        verbose_name="Estado",
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Existencias",
        help_text=(
            "Unidades físicas que tiene el organizador. CERO significa "
            "AGOTADO: un producto sin existencias no se puede pedir (RN-M06)."
        ),
    )
    reservado = models.PositiveIntegerField(
        default=0,
        verbose_name="Unidades reservadas",
        help_text=(
            "Unidades apartadas por pedidos pendientes. No se pueden vender "
            "hasta que el pedido se paga o se cancela (RN-M06)."
        ),
    )

    class Meta:
        db_table = "marketplace_producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="marketplace_producto_slug_unico_edicion",
            ),
            # Lo reservado nunca puede superar lo que hay: la BASE DE DATOS
            # lo garantiza, no la aplicación (RN-M06).
            models.CheckConstraint(
                condition=models.Q(reservado__lte=models.F("stock")),
                name="marketplace_producto_reservado_no_excede_stock",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre

    # ── Reglas de inventario (dominio, no presentación) ─────────────────────

    @property
    def disponible(self) -> int:
        """Las unidades que se pueden vender AHORA.

        Es `stock - reservado`: lo físico menos lo apartado por pedidos
        pendientes. Un producto `AGOTADO` tiene `disponible == 0` (RN-M06).
        """
        return max(0, self.stock - self.reservado)

    # ── Reglas de precio (dominio, no presentación) ─────────────────────────

    def oferta_activa(self, ahora=None) -> bool:
        """Si la oferta está vigente ahora.

        Una oferta exige `precio_oferta`. La ventana es OPCIONAL: sin
        `oferta_inicia` la oferta empieza ya; sin `oferta_termina` no caduca.
        """
        if self.precio_oferta is None:
            return False
        momento = ahora or timezone.now()
        if self.oferta_inicia is not None and self.oferta_inicia > momento:
            return False
        if self.oferta_termina is not None and self.oferta_termina < momento:
            return False
        return True

    def precio_efectivo(self, ahora=None) -> Decimal:
        """El precio que rige ahora: el de oferta si está vigente.

        El DOMINIO es la autoridad del precio: el cliente nunca lo calcula
        (RB-02 `SHOP-02`: "el precio mostrado tras la revalidación es el del
        backend").
        """
        if self.oferta_activa(ahora):
            return self.precio_oferta
        return self.precio
