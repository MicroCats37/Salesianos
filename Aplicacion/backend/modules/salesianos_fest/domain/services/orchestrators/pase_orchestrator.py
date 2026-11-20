"""`PaseOrchestrator` — fachada async del catálogo y de la compra de pases.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

Este orquestador hace TRES cosas y ninguna más:

1. Comprueba el ACCESO a un lote de pases antes de tocarlo: titular
   autenticado, administrador o token privado de ÁMBITO POR COMPRA.
2. Delega en `PaseFlujo` y `CompraPaseFlujo`.
3. Delega en `BeneficiarioFlujo` para la lectura de los derechos.

El resto de las reglas vive en los flujos.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import CompraPaseNoEncontradaError
from modules.salesianos_fest.domain.results.pase_result import (
    AdminPaseListaResult,
    CompraPaseResultado,
    PaseBeneficiariosResult,
    PaseCatalogoListaResult,
    PaseCompraDetalleResult,
    PaseDetalleResult,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import ComprarPaseData
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_acceso_service import (
    PaseAccesoService,
)
from modules.salesianos_fest.domain.services.flujos.beneficiario_flujo import (
    BeneficiarioFlujo,
)
from modules.salesianos_fest.domain.services.flujos.compra_pase_flujo import (
    CompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.pase_flujo import PaseFlujo


class PaseOrchestrator:
    """Fachada del catálogo y de la compra de pases."""

    @inject
    def __init__(
        self,
        flujo: PaseFlujo,
        compra_flujo: CompraPaseFlujo,
        beneficiario_flujo: BeneficiarioFlujo,
        pase_selector: PaseSelector,
        acceso: PaseAccesoService,
    ):
        self.flujo = flujo
        self.compra_flujo = compra_flujo
        self.beneficiario_flujo = beneficiario_flujo
        self.pase_selector = pase_selector
        self.acceso = acceso

    # ── Catálogo ────────────────────────────────────────────────────────────

    async def listar_pases(self, edicion_id) -> PaseCatalogoListaResult:
        """El catálogo de pases de la edición."""
        return await self.flujo.listar_pases(edicion_id)

    async def obtener_pase(self, edicion_id, pase_id) -> PaseDetalleResult:
        """El detalle de un pase."""
        return await self.flujo.obtener_pase(edicion_id, pase_id)

    # ── Compra ──────────────────────────────────────────────────────────────

    async def comprar_pase(
        self,
        actor,
        data: ComprarPaseData,
    ) -> CompraPaseResultado:
        """Compra (o recupera) un lote de pases.

        La compra puede ser de un INVITADO: no hace falta cuenta, pero
        tampoco se crea una. El comprador es el actor si la petición va
        autenticada, y la identidad civil declarada si no.
        """
        return await self.compra_flujo.comprar_pase(data, actor)

    # ── Lectura del lote ────────────────────────────────────────────────────

    async def obtener_compra(
        self,
        actor,
        compra_pase_id,
        token: str | None = None,
    ) -> PaseCompraDetalleResult:
        """El detalle de un lote de pases, si el actor puede abrirlo."""
        await self._verificar_acceso(actor, token, compra_pase_id)
        return await self.beneficiario_flujo.obtener_compra(compra_pase_id)

    async def listar_beneficiarios(
        self,
        actor,
        compra_pase_id,
        token: str | None = None,
    ) -> PaseBeneficiariosResult:
        """Los derechos de un lote de pases, si el actor puede abrirlo."""
        await self._verificar_acceso(actor, token, compra_pase_id)
        return await self.beneficiario_flujo.obtener_beneficiarios(compra_pase_id)

    # ── Administración ───────────────────────────────────────────────────────

    async def listar_compras(
        self,
        edicion_id=None,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AdminPaseListaResult:
        """El listado administrativo de lotes de pases.

        La autorización de ADMINISTRADOR la aplica la ruta (la puerta
        compartida `RequireAdmin`); este orquestador no la repite.
        """
        return await self.flujo.listar_compras(
            edicion_id,
            estado,
            page,
            page_size,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    async def _verificar_acceso(
        self,
        actor,
        token: str | None,
        compra_pase_id,
    ) -> None:
        """El acceso a un lote: titular, administrador o token del enlace."""
        compra_pase = await sync_to_async(self.pase_selector.obtener_compra_pase)(
            compra_pase_id
        )
        if compra_pase is None:
            raise CompraPaseNoEncontradaError()
        await sync_to_async(self.acceso.verificar)(
            actor=actor,
            token=token,
            compra_pase=compra_pase,
        )


__all__ = ["PaseOrchestrator"]
