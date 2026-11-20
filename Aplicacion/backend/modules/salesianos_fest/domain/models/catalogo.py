"""Catálogo de inscripción por EDICIÓN: promociones, categorías, disciplinas,
paquetes, beneficios y precios.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Invariantes del catálogo:

- **Todo el catálogo es de UNA EDICIÓN** (`RN-E01`): `Disciplina`, `Paquete`,
  `PaquetePrecio` y `Categoria` cuelgan de `eventos.Edicion`. No existe un
  paquete global.
- **La promoción es GLOBAL** (`D-CAT-04`): una cohorte de nacimiento es una
  propiedad de la persona, no de un evento. `Promocion` NO tiene edición.
- **El precio es un hecho del catálogo, no un literal del cliente**
  (`RN-C02`): `PaquetePrecio` congela un monto con su vigencia. Un paquete
  SIN precio vigente no está a la venta: no hay precio de reserva inventado
  (`FL-01` paso 3).
- **El precio es UNITARIO** (`D-CAT-01`): el monto del catálogo es el precio
  de UNA persona. El total lo deriva el servidor como `cantidad × precio`
  (`RN-C02`); el cliente declara cuántos participantes compra, nunca cuánto
  paga.
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
from django.db.models import F, Q

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import (
    EstadoCategoria,
    EstadoDisciplina,
    EstadoPaquete,
    EstadoPromocion,
    ModalidadDisciplina,
    ModoDisciplinas,
    TipoBeneficioPaquete,
    TipoPaquete,
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


class Promocion(BaseModel):
    """Cohorte de promoción (año de nacimiento) — GLOBAL.

    No cuelga de ninguna edición: una cohorte es una propiedad de la PERSONA
    (`D-CAT-04`). El `anio` es su clave natural y es único.

    El nombre es DESCRIPTIVO (la cohorte que el sitio anuncia); la banda
    competitiva la decide la `Categoria` de la edición, no la promoción.
    """

    anio = models.PositiveIntegerField(verbose_name="Año")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    estado = models.CharField(
        max_length=16,
        choices=EstadoPromocion.choices,
        default=EstadoPromocion.ACTIVA,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "fest_promocion"
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ["-anio"]
        constraints = [
            models.UniqueConstraint(
                fields=["anio"],
                name="fest_promocion_anio_unico",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.anio})"


class Categoria(BaseModel):
    """Banda competitiva (rango de promociones) de UNA edición.

    Es el mecanismo que convierte una cohorte en una banda con NOMBRE: el
    rango `[promocion_desde, promocion_hasta]` se guarda como AÑOS enteros,
    igual que en el legacy, para que la derivación cohorte → categoría no
    dependa de un JOIN con `Promocion`.
    """

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="categorias",
        verbose_name="Edición",
        help_text="La edición es el alcance: el catálogo no es global.",
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    promocion_desde = models.PositiveIntegerField(
        verbose_name="Promoción desde",
        help_text="Año de cohorte más reciente que entra en esta categoría.",
    )
    promocion_hasta = models.PositiveIntegerField(
        verbose_name="Promoción hasta",
        help_text="Año de cohorte más antiguo que entra en esta categoría.",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoCategoria.choices,
        default=EstadoCategoria.ACTIVA,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "fest_categoria"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["-promocion_hasta", "nombre"]
        constraints = [
            # El rango es un intervalo bien formado.
            models.CheckConstraint(
                condition=Q(promocion_desde__lte=F("promocion_hasta")),
                name="fest_categoria_rango_valido",
            ),
            # Una sola categoría ACTIVA por nombre y edición: el catálogo
            # histórico (inactiva) se conserva sin competir con el vigente.
            models.UniqueConstraint(
                fields=["edicion", "nombre"],
                condition=Q(estado=EstadoCategoria.ACTIVA),
                name="fest_categoria_nombre_unico_por_edicion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.edicion_id})"


class Paquete(BaseModel):
    """Paquete de inscripción ofrecido por UNA edición.

    El paquete NO dicta la cantidad de cupos que se compran: el comprador
    declara CUÁNTAS personas inscriben (`Paquete.minimo_compra_inicial` es
    el mínimo COMERCIAL) y el precio del catálogo es UNITARIO. El total lo
    deriva el servidor como `cantidad × precio_unitario` (`RN-C02`).

    `cupos_incluidos` sobrevive como hecho DECLARADO de la oferta (los
    cupos que incluye) y está DEPRECADO: no gobierna la compra. Es la
    transición que exige el espejo del frontend ya aplicado, que todavía lo
    publica.
    """

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
    tipo = models.CharField(
        max_length=16,
        choices=TipoPaquete.choices,
        default=TipoPaquete.PACK,
        verbose_name="Tipo",
        help_text=(
            "`PACK` es una oferta con beneficios; `DISCIPLINA` es la oferta "
            "de un solo torneo."
        ),
    )
    modo_disciplinas = models.CharField(
        max_length=16,
        choices=ModoDisciplinas.choices,
        default=ModoDisciplinas.ELEGIBLE,
        verbose_name="Modo de disciplinas",
        help_text=(
            "`FIJO` obliga a declarar EXACTAMENTE las disciplinas del "
            "paquete; `ELEGIBLE` deja elegir entre ellas."
        ),
    )
    cantidad_disciplinas = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad de disciplinas",
        help_text="Cuántas disciplinas puede declarar la inscripción con este paquete.",
    )
    cupos_incluidos = models.PositiveIntegerField(
        default=1,
        verbose_name="Cupos incluidos",
        help_text=(
            "Cupos que DECLARA la oferta del paquete. DEPRECADO: es el hecho "
            "de catálogo que la oferta incluye, NO la cantidad que el "
            "comprador compra. La cantidad la declara el comprador y su "
            "suelo comercial es `minimo_compra_inicial` (`D-CAT-01`)."
        ),
    )
    minimo_compra_inicial = models.PositiveIntegerField(
        default=1,
        verbose_name="Mínimo de compra inicial",
        help_text=(
            "Mínimo COMERCIAL de participantes en el alta. El cliente declara "
            "la cantidad; el servidor la contrasta con este mínimo."
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
            # Una oferta de una sola disciplina es de una sola disciplina.
            models.CheckConstraint(
                condition=~Q(
                    tipo=TipoPaquete.DISCIPLINA,
                    cantidad_disciplinas__gt=1,
                ),
                name="fest_paquete_disciplina_unica_cantidad",
            ),
            # Una oferta de una sola disciplina no es elegible: su disciplina
            # es la del paquete.
            models.CheckConstraint(
                condition=~Q(
                    tipo=TipoPaquete.DISCIPLINA,
                    modo_disciplinas=ModoDisciplinas.ELEGIBLE,
                ),
                name="fest_paquete_disciplina_modo_fijo",
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
    "Categoria",
    "Disciplina",
    "Paquete",
    "PaqueteBeneficio",
    "PaqueteDisciplina",
    "PaquetePrecio",
    "Promocion",
    "validar_monto_no_negativo",
]
