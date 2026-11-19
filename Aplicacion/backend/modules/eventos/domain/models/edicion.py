"""`Edicion` — la unidad de alcance (scope) de todo el dominio.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6, §10

Contrato de datos (FR-02 §3, literal):

    Edicion
      id: UUID            (pk)
      evento_id: UUID     FK → Evento
      nombre: str
      slug: str           único por evento
      anio: int
      estado: BORRADOR | PUBLICADA | CERRADA
      modulos_habilitados: list[str]   # claves de FR-02 §2.5
      fecha_inicio: date | null
      fecha_fin: date | null
      created_at, updated_at

Invariante: **como máximo una `Edicion` en estado `PUBLICADA` por `Evento`.**
Se expresa con una `UniqueConstraint` condicional sobre `(evento)` filtrada por
`estado = 'PUBLICADA'` — la base de datos es la autoridad, de modo que dos
publicaciones simultáneas no pueden coexistir.

`fecha_inicio` y `fecha_fin` son NULLABLES Y SIN SEMÁNTICA: el ciclo de vida
exacto de una edición no está ratificado (GOV-01-OPEN-03, owner A0 + producto).
"""

from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel

from modules.eventos.domain.constants import (
    MODULOS_HABILITABLES,
    EstadoEdicion,
)


def validar_modulos_habilitados(valor):
    """Valida que la lista de módulos sólo contenga claves conocidas.

    El valor por defecto de cada módulo es **deshabilitado** (FR-02 §2.5), así
    que la lista vacía es un estado válido. Una clave desconocida es un error
    de configuración, no un módulo nuevo silencioso.
    """
    if valor in (None, ""):
        return []
    if not isinstance(valor, (list, tuple)):
        raise ValidationError(
            "Los módulos habilitados deben ser una lista de claves conocidas."
        )
    desconocidos = [clave for clave in valor if clave not in MODULOS_HABILITABLES]
    if desconocidos:
        raise ValidationError(
            "Hay módulos habilitados que no pertenecen al catálogo del módulo."
        )
    return list(valor)


class Edicion(BaseModel):
    """Edición de un evento. Es la unidad de alcance del dominio."""

    evento = models.ForeignKey(
        "eventos.Evento",
        on_delete=models.PROTECT,
        related_name="ediciones",
        verbose_name="Evento",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la edición",
    )
    slug = models.SlugField(
        max_length=100,
        verbose_name="Identificador de la edición",
        help_text="Identificador único dentro del evento.",
    )
    anio = models.PositiveSmallIntegerField(
        verbose_name="Año de la edición",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoEdicion.choices,
        default=EstadoEdicion.BORRADOR,
        verbose_name="Estado",
    )
    modulos_habilitados = models.JSONField(
        default=list,
        blank=True,
        validators=[validar_modulos_habilitados],
        verbose_name="Módulos habilitados",
        help_text=(
            "Claves de módulos opcionales habilitadas para esta edición. "
            "Por defecto TODOS los módulos están deshabilitados."
        ),
    )
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de inicio",
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin",
    )

    class Meta:
        db_table = "eventos_edicion"
        verbose_name = "Edición"
        verbose_name_plural = "Ediciones"
        ordering = ["-anio", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "slug"],
                name="edicion_slug_unico_evento",
            ),
            models.UniqueConstraint(
                fields=["evento"],
                condition=models.Q(estado=EstadoEdicion.PUBLICADA),
                name="edicion_publicada_unica_evento",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.anio})"

    # ── Conveniencias triviales (sin lógica de negocio) ────────────────────

    @property
    def esta_publicada(self) -> bool:
        """Si la edición está en estado `PUBLICADA`."""
        return self.estado == EstadoEdicion.PUBLICADA

    def modulo_habilitado(self, clave: str) -> bool:
        """Si el módulo lógico indicado está habilitado en esta edición.

        Un módulo no habilitado no expone catálogo ni rutas de escritura
        (FR-02 §2.5). La ausencia de la clave significa DESHABILITADO: el
        valor por defecto nunca es "habilitado".
        """
        return clave in (self.modulos_habilitados or [])
