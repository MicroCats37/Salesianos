"""
Participacion — vínculo entre una persona inscrita y un equipo deportivo.

Cumple la Regla R11: una persona no puede participar activamente en la
misma disciplina del mismo evento a través de dos inscripciones distintas.

Los campos redundantes evento, disciplina y persona permiten una constraint
parcial a nivel de base de datos sin necesidad de JOINs.
La redundancia es controlada por el servicio — estos campos siempre se
sincronizan con sus orígenes lógicos.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

from core.models import BaseModel
from ..constants import EstadoParticipacionChoices, RolParticipanteChoices
from ..validators import es_genero_compatible_con_modalidad


class Participacion(BaseModel):
    """
    Representa la participación de una persona en un equipo deportivo.

    Attributes:
        inscripcion_persona: Vínculo inscripción-persona.
        equipo: Equipo al que pertenece.
        evento: Redundante — copia de inscripcion.equipo.inscripcion.evento
            (para constraint parcial R11 sin JOIN).
        disciplina: Redundante — copia de equipo.disciplina
            (para constraint parcial R11 sin JOIN).
        persona: Redundante — copia de inscripcion_persona.persona
            (para constraint parcial R11 sin JOIN).
        rol: J=Jugador, C=Capitán, D=Delegado.
        talla_camiseta: Talla de camiseta (S, M, L, XL, etc.).
        notas: Notas adicionales.
        estado: A=Activa, R=Retirada.
    """

    inscripcion_persona = models.ForeignKey(
        "InscripcionPersona",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Inscripción Persona",
    )
    equipo = models.ForeignKey(
        "Equipo",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Equipo",
    )
    evento = models.ForeignKey(
        "eventos.Evento",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Evento (redundante para R11)",
    )
    disciplina = models.ForeignKey(
        "Disciplina",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Disciplina (redundante para R11)",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Persona (redundante para R11)",
    )
    rol = models.CharField(
        max_length=1,
        choices=RolParticipanteChoices.choices,
        default=RolParticipanteChoices.JUGADOR,
        verbose_name="Rol",
    )
    talla_camiseta = models.CharField(
        max_length=3,
        blank=True,
        default="",
        verbose_name="Talla de camiseta",
    )
    notas = models.TextField(
        blank=True,
        default="",
        verbose_name="Notas",
    )
    estado = models.CharField(
        max_length=1,
        choices=EstadoParticipacionChoices.choices,
        default=EstadoParticipacionChoices.ACTIVA,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "participaciones"
        verbose_name = "Participación"
        verbose_name_plural = "Participaciones"
        ordering = ["equipo", "persona"]
        constraints = [
            # R11: no dos participaciones activas para la misma persona
            # en la misma disciplina del mismo evento
            models.UniqueConstraint(
                fields=["evento", "disciplina", "persona"],
                condition=Q(estado=EstadoParticipacionChoices.ACTIVA),
                name="unique_r11_evento_disciplina_persona_activa",
            ),
        ]
        indexes = [
            # R11 query path: busca participacion activa para (persona, evento, disciplina).
            # La constraint unique_r11 garantiza deduplicacion en escritura; este indice
            # cubre la lectura del camino sin costo de uniqueness checking.
            # pattern: Participacion.objects.filter(persona=X, evento=Y, disciplina=Z, estado='A')
            models.Index(
                fields=["persona", "evento", "disciplina", "estado"],
                name="idx_participacion_r11_path",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.persona} en {self.equipo} ({self.rol})"

    def clean(self):
        """Validate the discipline/gender compatibility of an ACTIVE participacion.

        Safety net for the write paths that bypass `ParticipacionCoreService`
        (Django Admin, management commands, ad-hoc scripts). The rule itself
        is NOT duplicated here: the shared predicate owns the matrix and this
        method only translates a rejection into a Django `ValidationError` so
        the admin reports it as a form error.

        Only the final state `A` is validated — retired history is allowed to
        stay incompatible so it can be remediated.
        """
        super().clean()

        if self.estado != EstadoParticipacionChoices.ACTIVA:
            return

        if not self.inscripcion_persona_id or not self.equipo_id:
            return

        genero = self.inscripcion_persona.persona.genero
        modalidad = self.equipo.disciplina.modalidad

        if es_genero_compatible_con_modalidad(genero, modalidad):
            return

        # A plain ValidationError IS Django's form-level (non field) error.
        # It must NOT be raised with a custom key: `ModelForm` only knows the
        # `__all__` key (NON_FIELD_ERRORS) and raises `ValueError` for any
        # other one, which would turn an admin rejection into a 500.
        raise ValidationError(
            "La modalidad de la disciplina no es compatible con el "
            "género de la persona."
        )
