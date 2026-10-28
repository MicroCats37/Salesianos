"""
PaseBeneficiario — the nominative entitlement of a person to a party pass.

One row = one slot of one batch (`CompraPase`) held by one `Persona`. It is
the analogue of `AsignacionCupo` for the sports domain, but it grants access
to the fiesta ONLY: it never creates a cupo, a participant, a team or a
sports balance.

Attributes:
    compra_pase: The batch this entitlement belongs to (FK PROTECT).
    evento: FK to the Evento — denormalised scope, so the "one active pass
        per (evento, persona)" rule can be enforced with a single index.
    persona: The person who holds the pass (FK PROTECT). A Persona is enough:
        a beneficiary needs NO Usuario and NO sports registration.
    slot: Immutable position of the entitlement inside the batch (1..cantidad).
    estado: ACTIVA or REVOCADA.
    asignado_por: The account that assigned the entitlement (audit, PROTECT).
    asignado_en: When the entitlement was assigned.
    revocado_por: The account that revoked it (audit, PROTECT, nullable).
    revocado_en: When it was revoked.
    motivo_revocacion: Why it was revoked.

Constraints (the guarantees the database itself enforces):
- unique (compra_pase, slot) — UNCONDITIONAL: a revoked slot is permanently
  consumed and can never be handed to somebody else.
- unique (compra_pase, persona) — UNCONDITIONAL: a person cannot be reused
  inside the same batch, not even after a revocation.
- partial unique (evento, persona) WHERE estado=ACTIVA — at most ONE active
  pass per person per event, across ALL purchases.

Invariants (service-level, NOT encoded as DB constraints):
- 1 <= slot <= CompraPase.cantidad.
- the assignment only happens on a PAID purchase (`Compra.estado=PAGADA`).
"""
from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento

from .compra_pase import CompraPase
from ..constants import EstadoPaseBeneficiarioChoices


class PaseBeneficiario(BaseModel):
    """
    The nominative right of a person to a party pass of one batch.
    """

    compra_pase = models.ForeignKey(
        CompraPase,
        on_delete=models.PROTECT,
        related_name="beneficiarios",
        verbose_name="Compra de pases",
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="beneficiarios_pase",
        verbose_name="Evento",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="pases_beneficiario",
        verbose_name="Beneficiario",
    )
    slot = models.PositiveIntegerField(
        verbose_name="Slot",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoPaseBeneficiarioChoices.choices,
        default=EstadoPaseBeneficiarioChoices.ACTIVA,
        verbose_name="Estado",
    )
    asignado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pases_asignados",
        verbose_name="Asignado por",
    )
    asignado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de asignación",
    )
    revocado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pases_revocados",
        null=True,
        blank=True,
        verbose_name="Revocado por",
    )
    revocado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de revocación",
    )
    motivo_revocacion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Motivo de revocación",
    )

    class Meta:
        db_table = "pases_beneficiarios"
        verbose_name = "Beneficiario de pase"
        verbose_name_plural = "Beneficiarios de pase"
        ordering = ["compra_pase", "slot"]
        constraints = [
            # El slot es INMUTABLE: un slot revocado queda consumido para
            # siempre y no puede volver a entregarse a otra persona.
            models.UniqueConstraint(
                fields=["compra_pase", "slot"],
                name="unique_pase_beneficiario_slot",
            ),
            # La misma persona no puede reutilizarse dentro del mismo lote,
            # ni siquiera después de una revocación (no hay transferencia).
            models.UniqueConstraint(
                fields=["compra_pase", "persona"],
                name="unique_pase_beneficiario_persona",
            ),
            # Como máximo un pase ACTIVO por persona y evento, entre TODAS
            # las compras.
            models.UniqueConstraint(
                fields=["evento", "persona"],
                condition=models.Q(estado=EstadoPaseBeneficiarioChoices.ACTIVA),
                name="unique_activa_pase_beneficiario_evento",
            ),
        ]
        indexes = [
            # Búsqueda de los derechos de una persona por evento.
            models.Index(
                fields=["persona", "estado"],
                name="idx_pase_ben_persona_estado",
            ),
            # Listado de los titulares de un lote.
            models.Index(
                fields=["compra_pase", "estado"],
                name="idx_pase_ben_compra_estado",
            ),
        ]

    def __str__(self) -> str:
        return f"PaseBeneficiario - {self.persona} - slot {self.slot} - {self.estado}"
