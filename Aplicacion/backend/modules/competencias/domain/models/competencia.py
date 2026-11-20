"""`Competencia` — un torneo de UNA edición y UNA disciplina.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Invariantes:

- **Todo es de UNA edición** (`RN-E01`): la competencia cuelga de
  `eventos.Edicion`, que es su alcance. No existe una competencia global.
- **La disciplina es de esa MISMA edición**: la disciplina es del catálogo de
  inscripción (`modules.salesianos_fest`), y ese catálogo es por edición.
- **La categoría es de esa MISMA edición**: la categoría (franja etaria) es
  también del catálogo de inscripción (`modules.salesianos_fest.Categoria`).
- **La identidad es (edición, disciplina, categoría, nombre)**, comparado sin
  distinguir mayúsculas: "Final" y "final" son la MISMA competencia. La
  CATEGORÍA es parte de la identidad porque DOS categorías distintas compiten
  en la MISMA disciplina: un cuadro Junior y un cuadro Sénior pueden llamarse
  igual y ser dos torneos DISTINTOS.
- La `fecha` es el DÍA de la competencia: una competencia ocurre en un día y el
  horario de sus encuentros vive dentro de ese día.

La competencia NO guarda el estado de sus equipos ni de sus encuentros: el
cuadro se deriva de ellos (`RN-K02`).
"""

from django.db import models
from django.db.models.functions import Lower

from modules.competencias.domain.constants import EstadoCompetencia
from modules.competencias.domain.models.base import CompetenciaBaseModel


class Competencia(CompetenciaBaseModel):
    """Un torneo de la edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Edición",
        help_text="La edición es el alcance: una competencia no es global.",
    )
    disciplina = models.ForeignKey(
        "salesianos_fest.Disciplina",
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Disciplina",
        help_text=(
            "La disciplina del torneo. Es la que fija la elegibilidad de los "
            "equipos (`RN-K01`)."
        ),
    )
    categoria = models.ForeignKey(
        "salesianos_fest.Categoria",
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Categoría",
        help_text=(
            "La categoría (franja etaria) del torneo. Junto con la disciplina, "
            "es la que fija la elegibilidad de los equipos (`RN-K01`)."
        ),
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    estado = models.CharField(
        max_length=20,
        choices=EstadoCompetencia.choices,
        default=EstadoCompetencia.PLANIFICADA,
        verbose_name="Estado",
    )
    fecha = models.DateField(
        verbose_name="Fecha",
        help_text="Día de la competencia. El horario de los encuentros vive dentro de este día.",
    )

    class Meta:
        db_table = "competencia_competencias"
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        ordering = ["-fecha", "nombre"]
        constraints = [
            # La identidad de una competencia: edición + disciplina + categoría
            # + nombre, comparado sin distinguir mayúsculas. La CATEGORÍA es
            # parte de la identidad: dos categorías de la misma disciplina son
            # dos torneos DISTINTOS.
            models.UniqueConstraint(
                "edicion",
                "disciplina",
                "categoria",
                Lower("nombre"),
                name="competencia_identidad_unica_por_edicion_disciplina_categoria",
            ),
        ]
        indexes = [
            models.Index(
                fields=["edicion", "disciplina", "estado", "fecha"],
                name="ix_cmp_edi_dis_est_fecha",
            ),
            models.Index(
                fields=["edicion", "categoria", "estado", "fecha"],
                name="ix_cmp_edi_cat_est_fecha",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.estado})"


__all__ = ["Competencia"]
