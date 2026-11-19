"""El POOL de una inscripción: participantes y equipos.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Invariantes:

- **Una participación `ACTIVA` ocupa UN cupo** de la inscripción (`RN-I03`).
  El contador `Inscripcion.cupos_asignados` es la verdad del saldo y lo
  mantienen los servicios con un incremento ATÓMICO condicional.
- **Una persona no participa dos veces en la misma inscripción**: lo
  garantiza la restricción única parcial `(inscripcion, persona) WHERE
  estado = ACTIVA`.
- **Una persona no participa dos veces en la misma disciplina de la misma
  edición**, aunque sea desde otra inscripción (solapamiento, `RN-I05`): lo
  garantiza la restricción única parcial `(edicion, disciplina, persona)
  WHERE estado = ACTIVA`. Para que esa restricción NO dependa de un `JOIN`,
  `edicion` y `disciplina` son campos REDUNDANTES que el servicio mantiene
  sincronizados con `inscripcion.edicion` y `equipo.disciplina`.
- **Todo es de UNA edición** (`RN-E01`): la participación, su equipo, su
  disciplina y su inscripción pertenecen a la misma edición.
- **Retirar NO es borrar**: la participación pasa a `RETIRADA` y conserva su
  historia. Retirar libera el cupo de ESA inscripción, pero NO anula la
  compra, NO devuelve dinero y NO cambia el inventario (`RN-I04`).

Correspondencia con el modelo de referencia: esta `Participacion` es la
`AsignacionCupo` del modelo heredado (`funcional/03` §1). El concepto se
conserva —el vínculo entre un cupo pagado y una persona dentro de una
inscripción— pero NO se copian sus columnas: el cupo no es una fila con
identidad propia, es una unidad de un contador (`RN-I03`). El nombre público
lo fija el contrato HTTP congelado: `participantes` / `participacion_id`
(`RT-IN-05`, `RT-IN-06`).

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6).
"""

from django.db import models

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import (
    EstadoParticipacion,
    RolParticipante,
)


class Participacion(BaseModel):
    """La participación de una persona en un equipo de una inscripción."""

    inscripcion = models.ForeignKey(
        "salesianos_fest.Inscripcion",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Inscripción",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="participaciones_inscripcion",
        verbose_name="Persona",
    )
    equipo = models.ForeignKey(
        "salesianos_fest.Equipo",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Equipo",
    )
    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="participaciones_inscripcion",
        verbose_name="Edición",
        help_text=(
            "Redundante: copia de `inscripcion.edicion`. Existe para que la "
            "restricción de solapamiento NO dependa de un JOIN."
        ),
    )
    disciplina = models.ForeignKey(
        "salesianos_fest.Disciplina",
        on_delete=models.PROTECT,
        related_name="participaciones_inscripcion",
        verbose_name="Disciplina",
        help_text=(
            "Redundante: copia de `equipo.disciplina`. Existe para que la "
            "restricción de solapamiento NO dependa de un JOIN."
        ),
    )
    rol = models.CharField(
        max_length=16,
        choices=RolParticipante.choices,
        default=RolParticipante.JUGADOR,
        verbose_name="Rol",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoParticipacion.choices,
        default=EstadoParticipacion.ACTIVA,
        verbose_name="Estado",
    )
    motivo = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo",
        help_text="Motivo de la retirada. Es técnico: no sale al cliente.",
    )
    retirada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Retirada en",
    )

    class Meta:
        db_table = "fest_participacion"
        verbose_name = "Participación"
        verbose_name_plural = "Participaciones"
        ordering = ["equipo_id", "created_at"]
        constraints = [
            # Una persona NO participa dos veces en la misma inscripción.
            models.UniqueConstraint(
                fields=["inscripcion", "persona"],
                condition=models.Q(estado=EstadoParticipacion.ACTIVA),
                name="fest_participacion_persona_unica_por_inscripcion",
            ),
            # Una persona NO participa dos veces en la misma disciplina de la
            # misma edición, ni siquiera desde otra inscripción.
            models.UniqueConstraint(
                fields=["edicion", "disciplina", "persona"],
                condition=models.Q(estado=EstadoParticipacion.ACTIVA),
                name="fest_participacion_disciplina_unica_por_edicion",
            ),
        ]
        indexes = [
            models.Index(
                fields=["inscripcion", "estado"],
                name="fest_participacion_insc_estado",
            ),
            models.Index(
                fields=["equipo", "estado"],
                name="fest_participacion_equipo_est",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.persona_id} en {self.equipo_id} ({self.estado})"


__all__ = ["Participacion"]
