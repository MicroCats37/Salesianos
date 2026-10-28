"""
AsignarBeneficiariosPaseFlujo — async flow for assigning the persons of a batch.

Async flow with ONE `transaction.atomic`. It materializes the NOMINATIVE
rights of a paid pass purchase: one person per immutable slot.

Rules:
1. the batch belongs to a purchase the caller owns (`Compra.responsable`);
2. the purchase MUST be PAGADA — a right is only granted over a paid pass;
3. only EXISTING personas are resolved (the flow NEVER creates a person out
   of free text sent by the client);
4. a person that already holds an ACTIVE right in this batch is an idempotent
   no-op (re-submitting the same list changes nothing);
5. a person whose right in this batch was REVOKED is refused: a paid pass is
   NOT transferable in v1;
6. a person that already holds an ACTIVE pass in the event (in ANOTHER
   purchase) is refused: at most one active pass per person per event;
7. the slots are immutable: the LOWEST free slots are allocated, and a
   revoked slot is never restored.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.exceptions import (
    PaseBeneficiarioDuplicadoError,
    PaseBeneficiarioNoEncontradoError,
    PaseBeneficiariosExcedidosError,
    PaseCompraNoEncontradaError,
    PaseCompraNoPagadaError,
    PaseNoTransferibleError,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.salesianos_fest.domain.results.pase_results import (
    PaseBeneficiariosAsignadosResult,
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


class AsignarBeneficiariosPaseFlujo:
    """
    Async flow for assigning the persons of a paid pass batch.
    """

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

    async def _asignar_beneficiarios(
        self,
        compra_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        beneficiario_ids: list[str],
    ) -> PaseBeneficiariosAsignadosResult:
        """
        Assign the given persons to the free slots of a batch.

        Args:
            compra_id: UUID of the commerce.Compra.
            responsable_id: Persona UUID of the caller (the buyer).
            actor_id: Usuario UUID that performs the assignment (audit).
            beneficiario_ids: Persona UUIDs, already resolved by the client.

        Raises:
            PaseCompraNoEncontradaError: the purchase is not a pass purchase.
            PaseCompraNoAutorizadaError: the caller is not the buyer.
            PaseCompraNoPagadaError: the purchase is not paid yet.
            PaseBeneficiarioNoEncontradoError: a person does not exist.
            PaseNoTransferibleError: a person already had a revoked right in
                this batch.
            PaseBeneficiarioDuplicadoError: a person already holds an active
                pass in the event.
            PaseBeneficiariosExcedidosError: there are not enough free slots.
        """
        return await sync_to_async(self._asignar_beneficiarios_sync)(
            compra_id, responsable_id, actor_id, beneficiario_ids
        )

    @transaction.atomic()
    def _asignar_beneficiarios_sync(
        self,
        compra_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        beneficiario_ids: list[str],
    ) -> PaseBeneficiariosAsignadosResult:
        """Sync body: the whole assignment inside one transaction."""
        # 1. Lock the batch and re-read it.
        linea = self.core.cargar_compra_pase(compra_id, bloquear=True)
        if linea is None:
            raise PaseCompraNoEncontradaError()

        compra = linea.compra

        # 2. Only the buyer may assign the persons of the batch.
        self.core.validar_propietario(compra, responsable_id)

        # 3. A right is only granted over a PAID purchase.
        if compra.estado != EstadoCompraChoices.PAGADA:
            raise PaseCompraNoPagadaError()

        # 4. Only EXISTING personas: the client resolves them, the flow never
        #    creates one.
        pedidas = self._deduplicar(beneficiario_ids)
        personas = self.selector.personas_existentes(pedidas)
        if len(personas) != len(pedidas):
            raise PaseBeneficiarioNoEncontradoError()

        # 5. Classify the requested persons against the batch. The rights of
        #    the batch are loaded ONCE (no N+1 over the requested persons).
        existentes = {
            existente.persona_id: existente
            for existente in self.selector.listar_por_compra_pase(str(linea.id))
        }
        ya_activos: set[str] = set()
        revocados: set[str] = set()
        for persona_id in pedidas:
            existente = existentes.get(persona_id)
            if existente is None:
                continue
            if existente.estado == EstadoPaseBeneficiarioChoices.ACTIVA:
                ya_activos.add(persona_id)
            else:
                revocados.add(persona_id)

        # 6. A paid pass is NOT transferable: a revoked right burns its slot
        #    and the person cannot be reused in the same batch.
        if revocados:
            raise PaseNoTransferibleError()

        nuevas = [persona_id for persona_id in pedidas if persona_id not in ya_activos]

        # 7. At most one ACTIVE pass per person and event, across purchases.
        for persona_id in nuevas:
            if self.selector.tiene_activo_en_evento(
                str(linea.evento_id),
                persona_id,
                excluir_compra_pase_id=str(linea.id),
            ):
                raise PaseBeneficiarioDuplicadoError()

        # 8. The slots are immutable: the lowest free ones are allocated and a
        #    revoked slot is never restored.
        slots_usados = self.selector.slots_usados(str(linea.id))
        libres = [
            slot for slot in range(1, linea.cantidad + 1) if slot not in slots_usados
        ]
        if len(nuevas) > len(libres):
            raise PaseBeneficiariosExcedidosError()

        # 9. Write the entitlements with their audit.
        for persona_id, slot in zip(nuevas, libres):
            PaseBeneficiario.objects.create(
                compra_pase=linea,
                evento=linea.evento,
                persona=personas[persona_id],
                slot=slot,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                asignado_por_id=actor_id,
            )

        # 10. Recompute the effective access of every person that received a
        #     pass: a beneficiary without inscripcion nor account gets the
        #     event accreditation too.
        for persona_id in nuevas:
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=str(linea.evento_id),
                persona_id=persona_id,
            )

        logger.info(
            "Pass beneficiaries assigned: compra=%s nuevos=%s ya_activos=%s",
            compra.id,
            len(nuevas),
            len(ya_activos),
        )

        # 10. The result reports the immutable slot accounting.
        activos, revocados_total = self.selector.contar_por_estado(str(linea.id))
        slots_usados_total = activos + revocados_total

        return PaseBeneficiariosAsignadosResult(
            compra_id=str(compra.id),
            cantidad_pases=linea.cantidad,
            activos=activos,
            revocados=revocados_total,
            slots_usados=slots_usados_total,
            slots_disponibles=max(0, linea.cantidad - slots_usados_total),
            asignados=len(nuevas),
            ya_asignados=len(ya_activos),
            beneficiarios=self.selector.listar_por_compra_pase(str(linea.id)),
        )

    @staticmethod
    def _deduplicar(beneficiario_ids: list[str]) -> list[str]:
        """Remove repeated ids, keeping the order of the request."""
        vistas: list[str] = []
        for persona_id in beneficiario_ids:
            if persona_id not in vistas:
                vistas.append(persona_id)
        return vistas
