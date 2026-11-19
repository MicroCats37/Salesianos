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

Este modelo NO declara existencias (stock): el inventario es de DOM-06
(`MovimientoInventario`), y el catálogo no inventa disponibilidad.
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
        ]

    def __str__(self) -> str:
        return self.nombre

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
