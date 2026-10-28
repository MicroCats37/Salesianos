"""
PaseBeneficiarioCoreService — sync operations of the pass entitlements.

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no `transaction.atomic` of its own, no write path. The caller
(the flujo) provides the transaction.

It owns the two operations the three beneficiary flows share: the locked read
of the batch and the ownership rule of the purchase.
"""
from typing import Optional

from django.utils import timezone
from injector import inject

from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.exceptions import (
    PaseCompraNoEncontradaError,
    PaseCompraNoAutorizadaError,
)
from modules.salesianos_fest.domain.models import CompraPase, PaseBeneficiario


class PaseBeneficiarioCoreService:
    """Sync operations over the pass entitlements."""

    @inject
    def __init__(self):
        pass

    def cargar_compra_pase(
        self,
        compra_id: str,
        bloquear: bool = False,
    ) -> Optional[CompraPase]:
        """
        Load the batch of a purchase, or None when there is none.

        A purchase that is not a pass purchase (a sports purchase) has no
        batch: it is simply not a pass purchase.

        `bloquear=True` locks the batch row (and NOT the joined nullable
        relations): the slot accounting of the batch is then stable while the
        transaction runs.
        """
        consulta = CompraPase.objects.filter(compra_id=compra_id).select_related(
            "compra",
            "compra__orden_pago",
            "compra__responsable",
            "pase",
            "evento",
        )
        if bloquear:
            consulta = consulta.select_for_update(of=("self",))
        return consulta.first()

    @staticmethod
    def validar_propietario(compra, responsable_id: Optional[str]) -> None:
        """
        Enforce that the caller owns the purchase.

        The owner of a pass purchase is its `Compra.responsable` — the buyer.
        There is no administrator bypass here: the administrative cancellation
        of a pass purchase is a separate, explicit operation.

        Raises:
            PaseCompraNoEncontradaError: the purchase has no owner at all.
            PaseCompraNoAutorizadaError: the caller is not the buyer.
        """
        if not compra.responsable_id:
            raise PaseCompraNoEncontradaError()
        if not responsable_id or str(compra.responsable_id) != str(responsable_id):
            raise PaseCompraNoAutorizadaError()

    def revocar_activos(
        self,
        compra,
        actor_id: Optional[str],
        motivo: str,
    ) -> list[tuple[str, str]]:
        """
        Revoke the ACTIVE pass entitlements of a purchase.

        This is the CANONICAL revocation of the pass rights: the ordinary
        administrative cancellation of a pass purchase AND the annulment of a
        manual payment approval both go through here, so the same rights are
        revoked and the same access is recomputed.

        Returns the affected (persona_id, evento_id) pairs so the caller can
        recompute the effective access of every affected person.
        """
        filas = list(
            PaseBeneficiario.objects
            .filter(
                compra_pase__compra_id=compra.id,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
            )
            .select_related("persona", "evento")
        )

        ahora = timezone.now()
        for fila in filas:
            fila.estado = EstadoPaseBeneficiarioChoices.REVOCADA
            fila.revocado_por_id = actor_id
            fila.revocado_en = ahora
            fila.motivo_revocacion = motivo
            fila.save(
                update_fields=[
                    "estado",
                    "revocado_por",
                    "revocado_en",
                    "motivo_revocacion",
                    "updated_at",
                ]
            )

        return [(str(fila.persona_id), str(fila.evento_id)) for fila in filas]
