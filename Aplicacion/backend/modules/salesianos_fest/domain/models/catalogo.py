"""Catálogo de inscripción por EDICIÓN: disciplinas, paquetes, beneficios y precios.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Invariantes del catálogo:

- **Todo el catálogo es de UNA EDICIÓN** (`RN-E01`): `Disciplina`, `Paquete`,
  `PaquetePrecio` cuelgan de `eventos.Edicion`. No existe un paquete global.
- **El precio es un hecho del catálogo, no un literal del cliente**
  (`RN-C02`): `PaquetePrecio` congela un monto con su vigencia. Un paquete
  SIN precio vigente no está a la venta: no hay precio de reserva inventado
  (`FL-01` paso 3).
- **Un beneficio es OFRECIDO, no disfrutado** (`RN-P01`):
  `PaqueteBeneficio` declara lo que el paquete ofrece; su concesión es otro
  hecho (`DOM-02`).
- Los modelos son planos y anémicos
  (`contract/django-app-architecture-contract.md` §6): campos, `Meta` y
  `__str__`. La lógica vive en los servicios.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import (
    EstadoDisciplina,
    EstadoPaquete,
    ModalidadDisciplina,
    TipoBeneficioPaquete,
)


def validar_monto_no_negativo(valor):
    """El precio de catálogo nunca es negativo."""
    if valor is None:
        return valor
    if valor < 0:
        raise ValidationError("El precio del paquete no puede ser negativo.")
    return valor


class Disciplina(BaseModel):
    """Disciplina deportiva ofrecida por UNA edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="disciplinas",
        verbose_name="Edición",
        help_text="La edición es el alcance: el catálogo no es global.",
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, verbose_name="Identificador")
    estado = models.CharField(
        max_length=16,
        choices=EstadoDisciplina.choices,
        default=EstadoDisciplina.ACTIVA,
        verbose_name="Estado",
    )
    modalidad = models.CharField(
        max_length=16,
        choices=ModalidadDisciplina.choices,
        default=ModalidadDisciplina.MIXTO,
        verbose_name="Modalidad",
    )
    minimo_por_equipo = models.PositiveIntegerField(
        default=1,
        verbose_name="Mínimo por equipo",
        help_text="Mínimo de participantes que exige un equipo de esta disciplina.",
    )
    maximo_por_equipo = models.PositiveIntegerField(
        default=20,
        verbose_name="Máximo por equipo",
    )

    class Meta:
        db_table = "fest_disciplina"
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="fest_disciplina_slug_unico_por_edicion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.edicion_id})"


class Paquete(BaseModel):
    """Paquete de inscripción ofrecido por UNA edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="paquetes",
        verbose_name="Edición",
        help_text="La edición es el alcance: el catálogo no es global.",
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, verbose_name="Identificador")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")
    estado = models.CharField(
        max_length=16,
        choices=EstadoPaquete.choices,
        default=EstadoPaquete.VIGENTE,
        verbose_name="Estado",
    )
    cupos_incluidos = models.PositiveIntegerField(
        default=1,
        verbose_name="Cupos incluidos",
        help_text=(
            "Cupos deportivos que otorga el paquete. Es la CANTIDAD que el "
            "servidor compra: el cliente no la impone (`RN-C02`)."
        ),
    )
    disciplinas = models.ManyToManyField(
        "salesianos_fest.Disciplina",
        through="salesianos_fest.PaqueteDisciplina",
        related_name="paquetes",
        verbose_name="Disciplinas permitidas",
    )

    class Meta:
        db_table = "fest_paquete"
        verbose_name = "Paquete"
        verbose_name_plural = "Paquetes"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="fest_paquete_slug_unico_por_edicion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.edicion_id})"


class PaqueteDisciplina(BaseModel):
    """Vínculo entre un paquete y las disciplinas que permite."""

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.CASCADE,
        related_name="disciplinas_vinculadas",
        verbose_name="Paquete",
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.PROTECT,
        related_name="paquetes_vinculados",
        verbose_name="Disciplina",
    )

    class Meta:
        db_table = "fest_paquete_disciplina"
        verbose_name = "Disciplina permitida por paquete"
        verbose_name_plural = "Disciplinas permitidas por paquete"
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "disciplina"],
                name="fest_paquete_disciplina_unica",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.paquete_id} → {self.disciplina_id}"


class PaqueteBeneficio(BaseModel):
    """Beneficio OFRECIDO por un paquete (`RN-P01`).

    Que el beneficio esté declarado aquí NO significa que esté concedido:
    la concesión es un hecho posterior, ligado al pago (`DOM-02`).
    """

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.CASCADE,
        related_name="beneficios",
        verbose_name="Paquete",
    )
    codigo = models.CharField(max_length=60, verbose_name="Código")
    nombre = models.CharField(max_length=160, verbose_name="Nombre")
    tipo = models.CharField(
        max_length=20,
        choices=TipoBeneficioPaquete.choices,
        default=TipoBeneficioPaquete.FIJO_INICIAL,
        verbose_name="Tipo",
        help_text=(
            "`FIJO_INICIAL` se otorga una sola vez por inscripción; `POR_CUPO` "
            "obedece la regla por cupo. La regla completa sigue ABIERTA "
            "(`PD-09`): aquí sólo se DECLARA el beneficio."
        ),
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    class Meta:
        db_table = "fest_paquete_beneficio"
        verbose_name = "Beneficio de paquete"
        verbose_name_plural = "Beneficios de paquete"
        ordering = ["paquete_id", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "codigo"],
                name="fest_paquete_beneficio_codigo_unico",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} ({self.paquete_id})"


class PaquetePrecio(BaseModel):
    """Precio de catálogo de un paquete, con su ventana de vigencia.

    El precio NO lo declara el cliente: lo resuelve el servidor contra el
    catálogo vigente y lo congela en la compra (`RN-C02`, `FR-04` §1.1).
    """

    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.CASCADE,
        related_name="precios",
        verbose_name="Paquete",
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validar_monto_no_negativo, MinValueValidator(0)],
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
        db_table = "fest_paquete_precio"
        verbose_name = "Precio de paquete"
        verbose_name_plural = "Precios de paquete"
        ordering = ["paquete_id", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(
                fields=["paquete", "vigente_desde"],
                name="fest_paquete_precio_inicio_unico",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.monto} {self.moneda} ({self.paquete_id})"


__all__ = [
    "Disciplina",
    "Paquete",
    "PaqueteBeneficio",
    "PaqueteDisciplina",
    "PaquetePrecio",
    "validar_monto_no_negativo",
]
