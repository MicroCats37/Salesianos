"""
RevocarBeneficiarioPaseFlujo — async flow for the permanent revocation of a right.

Async flow with ONE `transaction.atomic`. The revocation of a nominative right
is PERMANENT: the slot it occupied is consumed forever and the right is never
transferred to somebody else.

Rules:
1. the batch belongs to a purchase the caller owns (`Compra.responsable`);
2. the person must hold a right in that batch — an unknown person is a 404;
3. the revocation is IDEMPOTENT: revoking an already revoked right reports it
   as such instead of failing;
4. the revocation is AUDITED: actor, date and motive are kept forever.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from injector import inject

from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.exceptions import (
    PaseBeneficiarioNoEncontradoError,
    PaseCompraNoEncontradaError,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.salesianos_fest.domain.results.pase_results import (
    PaseBeneficiarioRevocadoResult,
)
from modules.salesianos_fest.domain.selectors.pase_beneficiario_selector import (
    PaseBeneficiarioSelector,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.pase_beneficiario_service import (
    PaseBeneficiarioCoreService,
)

logger = logging.getLogger(__name__)


class RevocarBeneficiarioPaseFlujo:
    """Async flow for the permanent revocation of a pass entitlement."""

    @inject
    def __init__(
        self,
        pase_beneficiario_core: PaseBeneficiarioCoreService,
        pase_beneficiario_selector: PaseBeneficiarioSelector,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.core = pase_beneficiario_core
        self.selector = pase_beneficiario_selector
        self.acreditacion_core = acreditacion_core

    async def _revocar_beneficiario(
        self,
        compra_id: str,
        persona_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        motivo: str,
    ) -> PaseBeneficiarioRevocadoResult:
        """
        Revoke the right of a person inside a batch, permanently.

        Args:
            compra_id: UUID of the commerce.Compra.
            persona_id: Persona UUID whose right is revoked.
            responsable_id: Persona UUID of the caller (the buyer).
            actor_id: Usuario UUID that performs the revocation (audit).
            motivo: Why the right is revoked (mandatory).

        Raises:
            PaseCompraNoEncontradaError: the purchase is not a pass purchase.
            PaseCompraNoAutorizadaError: the caller is not the buyer.
            PaseBeneficiarioNoEncontradoError: the person holds no right in
                this batch.
        """
        return await sync_to_async(self._revocar_beneficiario_sync)(
            compra_id, persona_id, responsable_id, actor_id, motivo
        )

    @transaction.atomic()
    def _revocar_beneficiario_sync(
        self,
        compra_id: str,
        persona_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        motivo: str,
    ) -> PaseBeneficiarioRevocadoResult:
        """Sync body: revoke the right inside one transaction."""
        # 1. Lock the batch and re-read it.
        linea = self.core.cargar_compra_pase(compra_id, bloquear=True)
        if linea is None:
            raise PaseCompraNoEncontradaError()

        # 2. Only the buyer may revoke the rights of the batch.
        self.core.validar_propietario(linea.compra, responsable_id)

        # 3. The person must hold a right in this batch.
        fila = (
            PaseBeneficiario.objects
            .select_for_update(of=("self",))
            .filter(compra_pase_id=str(linea.id), persona_id=persona_id)
            .first()
        )
        if fila is None:
            raise PaseBeneficiarioNoEncontradoError()

        # 4. Idempotent: an already revoked right is reported, not failed.
        ya_revocado = fila.estado == EstadoPaseBeneficiarioChoices.REVOCADA
        if not ya_revocado:
            fila.estado = EstadoPaseBeneficiarioChoices.REVOCADA
            fila.revocado_por_id = actor_id
            fila.revocado_en = timezone.now()
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
            logger.info(
                "Pass entitlement revoked: compra=%s persona=%s slot=%s",
                linea.compra_id,
                persona_id,
                fila.slot,
            )

        # 5. The slot stays consumed: a revoked right is never restored.
        activos, revocados = self.selector.contar_por_estado(str(linea.id))
        slots_usados = activos + revocados

        # 6. Recompute the effective access: revoking a pass removes ONLY that
        #    source — a sports benefit or an AUTORIZADA override may keep the
        #    fiesta access.
        self.acreditacion_core.sync_acreditacion_desde_compras(
            evento_id=str(linea.evento_id),
            persona_id=str(persona_id),
        )

        return PaseBeneficiarioRevocadoResult(
            compra_id=str(linea.compra_id),
            cantidad_pases=linea.cantidad,
            activos=activos,
            revocados=revocados,
            slots_usados=slots_usados,
            slots_disponibles=max(0, linea.cantidad - slots_usados),
            persona_id=str(persona_id),
            estado=fila.estado,
            revocado_en=fila.revocado_en,
            ya_revocado=ya_revocado,
        )
