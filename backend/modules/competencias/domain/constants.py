"""
Constants — choices (enums) for the competencias domain models.

Every state machine of the module is expressed here as a Django `TextChoices`
so the database, the API schemas and the admin share a single vocabulary.

The values are STABLE identifiers: they are persisted, filtered and indexed,
so they must not be renamed without a migration.
"""
from django.db import models


class EstadoCompetenciaChoices(models.TextChoices):
    """Lifecycle of a competition (spec: PLANIFICADA → EN_CURSO → FINALIZADA)."""

    PLANIFICADA = "PLANIFICADA", "Planificada"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoCompetenciaEquipoChoices(models.TextChoices):
    """State of a team inside the bracket of a competition."""

    ACTIVO = "ACTIVO", "Activo"
    RETIRADO = "RETIRADO", "Retirado"


class EstadoRondaChoices(models.TextChoices):
    """State of a round of the bracket."""

    ACTIVA = "ACTIVA", "Activa"
    INVALIDADA = "INVALIDADA", "Invalidada"


class EstadoEncuentroChoices(models.TextChoices):
    """Lifecycle of a single encounter of the bracket."""

    BORRADOR = "BORRADOR", "Borrador"
    PROGRAMADO = "PROGRAMADO", "Programado"
    EN_CURSO = "EN_CURSO", "En curso"
    SUSPENDIDO = "SUSPENDIDO", "Suspendido"
    FINALIZADO = "FINALIZADO", "Finalizado"
    CANCELADO = "CANCELADO", "Cancelado"


class EstadoPreSuspensionChoices(models.TextChoices):
    """States an encounter can be resumed from after a suspension.

    Only the non-terminal states are accepted: a suspended encounter may be
    resumed to the state it had before the suspension, and that state can
    never be a terminal one (FINALIZADO / CANCELADO).
    """

    BORRADOR = "BORRADOR", "Borrador"
    PROGRAMADO = "PROGRAMADO", "Programado"
    EN_CURSO = "EN_CURSO", "En curso"


class SlotDestinoChoices(models.TextChoices):
    """Slot of the linked encounter that receives the propagated winner."""

    PARTICIPANTE_1 = "PARTICIPANTE_1", "Participante 1"
    PARTICIPANTE_2 = "PARTICIPANTE_2", "Participante 2"


#: Field of `Encuentro` that holds each destination slot. The propagation
#: and the correction read and write the slot through this mapping, so the
#: two commands never disagree about which field they are talking about.
CAMPOS_DE_SLOT: dict[str, str] = {
    SlotDestinoChoices.PARTICIPANTE_1: "participante_1",
    SlotDestinoChoices.PARTICIPANTE_2: "participante_2",
}
