"""
AcreditacionEvento — acreditacion efectiva de una persona a un evento.

Representa permisos efectivos de ACCESO (no es un derecho de cupo).
Es GLOBAL: una sola fila por (evento, persona) sin importar cuantas
inscripciones/compras la financian.

Attributes:
    evento: Evento de la acreditacion.
    persona: Persona acreditada.
    estado: PENDIENTE, ACTIVA, SUSPENDIDA, REVOCADA.
    acceso_fiesta: Boolean - derecho efectivo de acceso a fiesta.
    acceso_box: Boolean (nullable) - control individual de zona box (deferred).
    autorizacion_fiesta: AUTOMATICA, AUTORIZADA, BLOQUEADA.
        Precedencia: BLOQUEADA > AUTORIZADA > AUTOMATICA
    habilitado: Boolean nullable - override general de admin.
    codigo_qr: UUID unique - token no adivinable para escaneo.
    observacion: Nota administrativa (nullable).

Constraints:
- Unique: (evento, persona) - one accreditation per person per event
- The estado is the effective operational state; habilitado is a manual override
- Precedence: estado=REVOCADA or habilitado=False blocks regardless of acceso_fiesta

Override rules:
- Admin can allow fiesta to someone who only bought sport, or block someone who paid
- Override must NOT be cleared on next sync - author, reason, and timestamp are auditable
- New purchase or retirement does NOT clear admin override
"""
import uuid

from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from ..constants import EstadoAcreditacionChoices, AutorizacionFiestaChoices


class AcreditacionEvento(BaseModel):
    """
    Acreditacion efectiva de una persona a un evento.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="acreditaciones",
        verbose_name="Evento",
    )
    persona = models.ForeignKey(
        Persona,
        on_delete=models.PROTECT,
        related_name="acreditaciones_evento",
        verbose_name="Persona",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoAcreditacionChoices.choices,
        default=EstadoAcreditacionChoices.PENDIENTE,
        verbose_name="Estado",
    )
    acceso_fiesta = models.BooleanField(
        default=False,
        verbose_name="Acceso a fiesta",
    )
    acceso_box = models.BooleanField(
        blank=True,
        null=True,
        verbose_name="Acceso a box (deferred)",
    )
    autorizacion_fiesta = models.CharField(
        max_length=15,
        choices=AutorizacionFiestaChoices.choices,
        default=AutorizacionFiestaChoices.AUTOMATICA,
        verbose_name="Autorizacion de fiesta",
    )
    habilitado = models.BooleanField(
        blank=True,
        null=True,
        verbose_name="Override general de admin",
    )
    codigo_qr = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        verbose_name="Codigo QR",
    )
    observacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Observacion administrativa",
    )

    class Meta:
        db_table = "acreditaciones_evento"
        verbose_name = "Acreditacion de Evento"
        verbose_name_plural = "Acreditaciones de Evento"
        ordering = ["evento", "persona"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "persona"],
                name="unique_evento_persona_acreditacion",
            ),
        ]

    def __str__(self) -> str:
        return f"Acreditacion {self.evento} - {self.persona} ({self.estado})"
