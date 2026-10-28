"""
ObtenerCompraPaseFlujo — async flow for reading a pass purchase.

Read-only flow: it opens no transaction and writes nothing.

The purchase is OWNER-ONLY: only `Compra.responsable` (the buyer) may read
it. The commercial state and the frozen values come from the persisted
snapshot — they never change after the purchase.
"""
from asgiref.sync import sync_to_async
from dataclasses import replace
from injector import inject

from modules.salesianos_fest.domain.exceptions import (
    PaseCompraNoAutorizadaError,
    PaseCompraNoEncontradaError,
)
from modules.salesianos_fest.domain.results.pase_results import PaseCompraDetalleResult
from modules.salesianos_fest.domain.selectors.compra_pase_selector import (
    CompraPaseSelector,
)
from modules.salesianos_fest.domain.selectors.pase_beneficiario_selector import (
    PaseBeneficiarioSelector,
)


class ObtenerCompraPaseFlujo:
    """Async flow that resolves the state of a pass purchase."""

    @inject
    def __init__(
        self,
        compra_pase_selector: CompraPaseSelector,
        pase_beneficiario_selector: PaseBeneficiarioSelector,
    ):
        self.compra_pase_selector = compra_pase_selector
        self.pase_beneficiario_selector = pase_beneficiario_selector

    async def _obtener_compra_pase(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseCompraDetalleResult:
        """
        Return the state of a pass purchase for its owner.

        Args:
            compra_id: UUID of the commerce.Compra.
            responsable_id: Persona UUID of the caller.

        Raises:
            PaseCompraNoEncontradaError: the purchase does not exist or is not
                a pass purchase.
            PaseCompraNoAutorizadaError: the caller is not the owner.
        """
        return await sync_to_async(self._obtener_compra_pase_sync)(
            compra_id, responsable_id
        )

    def _obtener_compra_pase_sync(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseCompraDetalleResult:
        """Sync body: load the detail and enforce the ownership rule."""
        detalle = self.compra_pase_selector.obtener_detalle(compra_id)
        if detalle is None:
            raise PaseCompraNoEncontradaError()

        if not responsable_id or detalle.responsable_id != str(responsable_id):
            raise PaseCompraNoAutorizadaError()

        # La contabilidad de slots es INMUTABLE: un slot revocado sigue
        # consumido y no vuelve a estar disponible.
        activos, revocados = self.pase_beneficiario_selector.contar_por_estado(
            str(detalle.compra_pase_id)
        )
        slots_usados = activos + revocados

        return replace(
            detalle,
            beneficiarios_asignados=activos,
            beneficiarios_pendientes=max(0, detalle.cantidad - slots_usados),
        )
