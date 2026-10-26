"""
AsignacionCupo — vincula un cupo pagado de una Compra a una persona registrada.

Se materializa a partir de la capacidad pagada de la inscripcion: al confirmar
el pago (commerce.Compra=PAGADA) y al pre-registrar a la persona en el pool.
La asignacion es un derecho standing de la persona, no una foto del momento
del pago. No se crean filas vacias - la cantidad de cupos vive en
CompraInscripcion.cantidad.

Attributes:
    inscripcion: Inscripcion duena del cupo (FK PROTECT).
    compra: commerce.Compra origen del cupo pagado (FK PROTECT).
    inscripcion_persona: Persona asignada a este cupo (FK PROTECT).
    estado: ACTIVA (cupo ocupado), LIBERADA (retirado pero compra sigue paga),
            REVOCADA (revocado por admin).
    motivo: Razon de liberacion/revocacion (nullable).
    liberada_en: Timestamp de liberacion (nullable).

Constraints:
- Unique constraint partial: (inscripcion, inscripcion_persona) WHERE estado=ACTIVA
  → previene doble asignacion activa de la misma persona en la misma inscripcion.
- Unique constraint partial: (compra, inscripcion_persona) WHERE estado=ACTIVA
  → previene que la misma persona sea asignada dos veces desde la misma compra pagada.

Indexes:
- (compra, estado)        → lista asignaciones activas por compra (CrearAsignacionesFlujo).
- (inscripcion_persona, estado) → lista asignaciones activas por persona-inscripcion.
- (inscripcion, estado)   → lista asignaciones por inscripcion.

Invariants (service-level, NOT encoded as DB constraints):
- COUNT(AsignacionCupo WHERE compra=X AND estado=ACTIVA) <= CompraInscripcion.cantidad
  → Servicio usa SELECT FOR UPDATE en Compra + verificacion en transaction atomica.
- No empty rows - AsignacionCupo only created when a registered person is assigned.
"""
from django.db import models

from core.models import BaseModel
from .inscripcion import Inscripcion
from .inscripcion_persona import InscripcionPersona
from ..constants import EstadoAsignacionCupoChoices


class AsignacionCupo(BaseModel):
    """
    Vincula un cupo pagado de una Compra a una persona registrada.
    """

    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.PROTECT,
        related_name="asignaciones_cupo",
        verbose_name="Inscripcion",
    )
    compra = models.ForeignKey(
        "commerce.Compra",
        on_delete=models.PROTECT,
        related_name="asignaciones_cupo",
        verbose_name="Compra generica",
    )
    inscripcion_persona = models.ForeignKey(
        InscripcionPersona,
        on_delete=models.PROTECT,
        related_name="asignaciones_cupo",
        verbose_name="Persona asignada",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoAsignacionCupoChoices.choices,
        default=EstadoAsignacionCupoChoices.ACTIVA,
        verbose_name="Estado",
    )
    motivo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de liberacion/revocacion",
    )
    liberada_en = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de liberacion",
    )

    class Meta:
        db_table = "asignaciones_cupo"
        verbose_name = "Asignacion de Cupo"
        verbose_name_plural = "Asignaciones de Cupo"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion", "inscripcion_persona"],
                condition=models.Q(estado=EstadoAsignacionCupoChoices.ACTIVA),
                name="unique_activa_inscripcion_persona",
            ),
            # Previene doble asignacion activa de la misma persona desde la misma compra.
            # Distinto de unique_activa_inscripcion_persona: aqui el alcance es la compra,
            # no la inscripcion. Una misma persona puede tener AsignacionCupo ACTIVA en
            # la misma inscripcion si viene de compras DISTINTAS (distinto origen de cupo).
            models.UniqueConstraint(
                fields=["compra", "inscripcion_persona"],
                condition=models.Q(estado=EstadoAsignacionCupoChoices.ACTIVA),
                name="unique_activa_compra_persona",
            ),
        ]
        indexes = [
            # Para queries de asignaciones activas por compra (usado en CrearAsignacionesFlujo).
            models.Index(fields=["compra", "estado"], name="idx_asign_cupo_compra_estado"),
            # Para queries de asignaciones activas por persona-inscripcion (usado en
            # obtener_asignacion_activa_por_persona, validacion de cupo activo).
            models.Index(fields=["inscripcion_persona", "estado"], name="idx_asign_cupo_ip_estado"),
            # Para queries de todas las asignaciones de una inscripcion (sin filtro de estado).
            # El nombre no puede superar los 30 caracteres (models.E034).
            models.Index(fields=["inscripcion", "estado"], name="idx_asign_cupo_insc_estado"),
        ]

    def __str__(self) -> str:
        return f"AsignacionCupo {self.inscripcion_persona} - {self.estado}"
