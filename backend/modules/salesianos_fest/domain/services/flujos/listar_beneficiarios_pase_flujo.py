"""
ListarBeneficiariosPaseFlujo — async flow for listing the persons of a batch.

Read-only flow: it opens no transaction and writes nothing.

Only the buyer (`Compra.responsable`) may read the beneficiaries of the
purchase. The slot accounting is IMMUTABLE: a revoked slot stays consumed and
is never restored, so `slots_disponibles` only grows when a NEW batch is
bought.
"""
from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import PaseCompraNoEncontradaError
from modules.salesianos_fest.domain.results.pase_results import (
    PaseBeneficiariosListaResult,
)
from modules.salesianos_fest.domain.selectors.pase_beneficiario_selector import (
    PaseBeneficiarioSelector,
)
from modules.salesianos_fest.domain.services.core.pase_beneficiario_service import (
    PaseBeneficiarioCoreService,
)


class ListarBeneficiariosPaseFlujo:
    """Async flow that lists the beneficiaries of a pass batch."""

    @inject
    def __init__(
        self,
        pase_beneficiario_core: PaseBeneficiarioCoreService,
        pase_beneficiario_selector: PaseBeneficiarioSelector,
    ):
        self.core = pase_beneficiario_core
        self.selector = pase_beneficiario_selector

    async def _listar_beneficiarios(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseBeneficiariosListaResult:
        """
        Return the beneficiaries of a batch with the slot accounting.

        Raises:
            PaseCompraNoEncontradaError: the purchase is not a pass purchase.
            PaseCompraNoAutorizadaError: the caller is not the buyer.
        """
        return await sync_to_async(self._listar_beneficiarios_sync)(
            compra_id, responsable_id
        )

    def _listar_beneficiarios_sync(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseBeneficiariosListaResult:
        """Sync body: load the batch, check the owner and count the slots."""
        linea = self.core.cargar_compra_pase(compra_id)
        if linea is None:
            raise PaseCompraNoEncontradaError()

        self.core.validar_propietario(linea.compra, responsable_id)

        activos, revocados = self.selector.contar_por_estado(str(linea.id))
        slots_usados = activos + revocados

        return PaseBeneficiariosListaResult(
            compra_id=str(linea.compra_id),
            cantidad_pases=linea.cantidad,
            activos=activos,
            revocados=revocados,
            slots_usados=slots_usados,
            slots_disponibles=max(0, linea.cantidad - slots_usados),
            beneficiarios=self.selector.listar_por_compra_pase(str(linea.id)),
        )
