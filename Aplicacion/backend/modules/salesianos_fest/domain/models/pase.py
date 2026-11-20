"""Catálogo de PASES por EDICIÓN: el producto de entrada y su precio.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Invariantes del catálogo de pases:

- **Todo el catálogo es de UNA EDICIÓN** (`RN-E01`): `Pase` y `PasePrecio`
  cuelgan de `eventos.Edicion`. No existe un pase global.
- **El precio es un hecho del catálogo, no un literal del cliente**
  (`RN-C02`): `PasePrecio` congela un monto con su vigencia. Un pase SIN
  precio vigente NO está a la venta: no hay precio de reserva inventado.
- **El tipo de pase NO decide quién lo usa**: el comprador y el asistente
  pueden ser personas distintas (`RN-P04`). El comprador es el TITULAR de la
  compra; el asistente es el BENEFICIARIO del derecho.

Este archivo NO modela el beneficio grupal `BOX`: su titularidad y su uso
siguen ABIERTOS (`PD-01`) y modelarlos sería inventar una política. El
`Pase` no tiene ninguna marca de `BOX` a propósito.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6): campos, `Meta` y
`__str__`. La lógica vive en los servicios.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import EstadoPase


def validar_monto_pase_no_negativo(valor):
    """El precio de catálogo de un pase nunca es negativo."""
    if valor is None:
        return valor
    if valor < 0:
        raise ValidationError("El precio del pase no puede ser negativo.")
    return valor


class Pase(BaseModel):
    """Tipo de entrada que se compra por unidades y se asigna a una persona.

    Un `Pase` es el CONCEPTO del catálogo (el «Pase FEST», el «Pase VIP»).
    No es un derecho: el derecho de entrada es `PaseBeneficiario`, y el
    lote comprado es `CompraPase`.
    """

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="pases",
        verbose_name="Edición",
    )
    nombre = models.CharField(
        max_length=160,
        verbose_name="Nombre",
    )
    slug = models.SlugField(
        max_length=80,
        verbose_name="Identificador",
        help_text="Identificador del pase dentro de la edición.",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoPase.choices,
        default=EstadoPase.VIGENTE,
        verbose_name="Estado",
        help_text=(
            "`RETIRADO` conserva el catálogo histórico pero no se ofrece ni "
            "se compra."
        ),
    )

    class Meta:
        db_table = "fest_pase"
        verbose_name = "Pase"
        verbose_name_plural = "Pases"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="fest_pase_slug_unico_por_edicion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.edicion_id})"


class PasePrecio(BaseModel):
    """Precio de catálogo de un pase, con su ventana de vigencia.

    El precio NO lo declara el cliente: lo resuelve el servidor contra el
    catálogo vigente y lo congela en la compra (`RN-C02`, `FR-04` §1.1).
    """

    pase = models.ForeignKey(
        Pase,
        on_delete=models.CASCADE,
        related_name="precios",
        verbose_name="Pase",
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validar_monto_pase_no_negativo, MinValueValidator(0)],
        verbose_name="Monto",
    )
    moneda = models.CharField(
        max_length=3,
        default="PEN",
        verbose_name="Moneda",
        help_text="Código ISO-4217.",
    )
    vigente_desde = models.DateField(verbose_name="Vigente desde")
    vigente_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vigente hasta",
        help_text="Vacío significa vigencia abierta.",
    )

    class Meta:
        db_table = "fest_pase_precio"
        verbose_name = "Precio de pase"
        verbose_name_plural = "Precios de pase"
        ordering = ["pase_id", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(
                fields=["pase", "vigente_desde"],
                name="fest_pase_precio_inicio_unico",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.monto} {self.moneda} ({self.pase_id})"


__all__ = [
    "Pase",
    "PasePrecio",
    "validar_monto_pase_no_negativo",
]
