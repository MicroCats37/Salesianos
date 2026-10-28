"""
PaseBeneficiarioSelector — queries for the nominative entitlements of a pass.

Read-only: it never writes and never transforms to the HTTP layer.

The selector owns the READ side of the three rules of the entitlement:
which slots are consumed, which persons already hold a right in this batch and
which persons already hold an ACTIVE pass in the event (across purchases).
"""
from typing import Optional

from modules.usuarios.domain.models import Persona

from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.salesianos_fest.domain.results.pase_results import (
    PaseBeneficiarioResult,
)


class PaseBeneficiarioSelector:
    """Query interface for the pass beneficiaries."""

    def listar_por_compra_pase(self, compra_pase_id: str) -> list[PaseBeneficiarioResult]:
        """Return the beneficiaries of a batch, ordered by slot."""
        filas = (
            PaseBeneficiario.objects
            .filter(compra_pase_id=compra_pase_id)
            .select_related("persona")
            .order_by("slot")
        )
        return [self._mapear(fila) for fila in filas]

    def slots_usados(self, compra_pase_id: str) -> set[int]:
        """
        Return the slots already consumed by a batch.

        A revoked slot stays consumed: the entitlement is NOT transferable, so
        the slot is burned forever.
        """
        return set(
            PaseBeneficiario.objects
            .filter(compra_pase_id=compra_pase_id)
            .values_list("slot", flat=True)
        )

    def tiene_activo_en_evento(
        self,
        evento_id: str,
        persona_id: str,
        excluir_compra_pase_id: Optional[str] = None,
    ) -> bool:
        """
        Return True when the person already holds an ACTIVE pass in the event.

        The check spans ALL purchases: at most one active pass per person per
        event.
        """
        consulta = PaseBeneficiario.objects.filter(
            evento_id=evento_id,
            persona_id=persona_id,
            estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        )
        if excluir_compra_pase_id is not None:
            consulta = consulta.exclude(compra_pase_id=excluir_compra_pase_id)
        return consulta.exists()

    def contar_por_estado(self, compra_pase_id: str) -> tuple[int, int]:
        """Return the (activos, revocados) counts of a batch."""
        activos = PaseBeneficiario.objects.filter(
            compra_pase_id=compra_pase_id,
            estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        ).count()
        revocados = PaseBeneficiario.objects.filter(
            compra_pase_id=compra_pase_id,
            estado=EstadoPaseBeneficiarioChoices.REVOCADA,
        ).count()
        return activos, revocados

    def personas_existentes(self, persona_ids: list[str]) -> dict[str, Persona]:
        """
        Return the EXISTING personas of the given ids, keyed by id.

        The lookup is ONLY by id: the flow never creates a persona out of free
        text sent by the client.
        """
        return {
            str(persona.id): persona
            for persona in Persona.objects.filter(id__in=persona_ids)
        }

    @staticmethod
    def _mapear(fila) -> PaseBeneficiarioResult:
        """Map a beneficiary row into its result DTO."""
        persona = fila.persona
        return PaseBeneficiarioResult(
            persona_id=str(persona.id),
            nombre_completo=f"{persona.nombres} {persona.apellidos}".strip(),
            tipo_documento=persona.tipo_documento,
            numero_documento=persona.numero_documento,
            slot=fila.slot,
            estado=fila.estado,
            asignado_en=fila.asignado_en,
            revocado_en=fila.revocado_en,
            motivo_revocacion=fila.motivo_revocacion,
        )
