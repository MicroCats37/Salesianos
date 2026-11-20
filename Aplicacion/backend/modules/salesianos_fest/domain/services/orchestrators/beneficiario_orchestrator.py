"""`BeneficiarioOrchestrator` — fachada async de la asignación de beneficiarios.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

Este orquestador hace DOS cosas y ninguna más:

1. Comprueba el ACCESO al lote de pases antes de tocarlo (titular
   autenticado, administrador o token privado de ÁMBITO POR COMPRA).
2. Delega en `BeneficiarioFlujo`.

El resto de las reglas vive en el flujo.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import CompraPaseNoEncontradaError
from modules.salesianos_fest.domain.results.pase_result import (
    PaseBeneficiarioRevocadoResult,
    PaseBeneficiariosResult,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import (
    AsignarBeneficiarioData,
    RevocarBeneficiarioData,
)
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_acceso_service import (
    PaseAccesoService,
)
from modules.salesianos_fest.domain.services.flujos.beneficiario_flujo import (
    BeneficiarioFlujo,
)


class BeneficiarioOrchestrator:
    """Fachada de la asignación y la revocación de beneficiarios."""

    @inject
    def __init__(
        self,
        flujo: BeneficiarioFlujo,
        pase_selector: PaseSelector,
        acceso: PaseAccesoService,
    ):
        self.flujo = flujo
        self.pase_selector = pase_selector
        self.acceso = acceso

    async def asignar_beneficiario(
        self,
        actor,
        compra_pase_id,
        data: AsignarBeneficiarioData,
        token: str | None = None,
    ) -> PaseBeneficiariosResult:
        """Asigna un pase del lote a una persona, si el actor puede abrirlo."""
        await self._verificar_acceso(actor, token, compra_pase_id)
        return await self.flujo.asignar_beneficiario(
            compra_pase_id,
            data,
            actor,
        )

    async def revocar_beneficiario(
        self,
        actor,
        compra_pase_id,
        persona_id,
        data: RevocarBeneficiarioData,
        token: str | None = None,
    ) -> PaseBeneficiarioRevocadoResult:
        """Revoca un derecho de entrada, si el actor puede abrir el lote."""
        await self._verificar_acceso(actor, token, compra_pase_id)
        return await self.flujo.revocar_beneficiario(
            compra_pase_id,
            persona_id,
            data,
            actor,
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


__all__ = ["BeneficiarioOrchestrator"]
