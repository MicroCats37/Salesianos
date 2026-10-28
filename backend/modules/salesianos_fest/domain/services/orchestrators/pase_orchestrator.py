"""
PaseOrchestrator — async thin facade for the party-pass catalogue and purchase.

Thin async facade that only delegates to the flows.
No business logic here — only delegation.
"""
from injector import inject

from modules.salesianos_fest.domain.results.pase_results import (
    PaseCatalogoResult,
    PaseCompraCreadaResult,
    PaseCompraDetalleResult,
    PaseBeneficiariosListaResult,
    PaseBeneficiariosAsignadosResult,
    PaseBeneficiarioRevocadoResult,
)
from modules.salesianos_fest.domain.services.flujos.crear_compra_pase_flujo import (
    CrearCompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.listar_pases_flujo import (
    ListarPasesFlujo,
)
from modules.salesianos_fest.domain.services.flujos.obtener_compra_pase_flujo import (
    ObtenerCompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.asignar_beneficiarios_pase_flujo import (
    AsignarBeneficiariosPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.listar_beneficiarios_pase_flujo import (
    ListarBeneficiariosPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.revocar_beneficiario_pase_flujo import (
    RevocarBeneficiarioPaseFlujo,
)


class PaseOrchestrator:
    """Thin async facade for Pase catalogue, purchase and beneficiary operations."""

    @inject
    def __init__(
        self,
        listar_pases_flujo: ListarPasesFlujo,
        crear_compra_pase_flujo: CrearCompraPaseFlujo,
        obtener_compra_pase_flujo: ObtenerCompraPaseFlujo,
        asignar_beneficiarios_pase_flujo: AsignarBeneficiariosPaseFlujo,
        listar_beneficiarios_pase_flujo: ListarBeneficiariosPaseFlujo,
        revocar_beneficiario_pase_flujo: RevocarBeneficiarioPaseFlujo,
    ):
        self.listar_pases_flujo = listar_pases_flujo
        self.crear_compra_pase_flujo = crear_compra_pase_flujo
        self.obtener_compra_pase_flujo = obtener_compra_pase_flujo
        self.asignar_beneficiarios_pase_flujo = asignar_beneficiarios_pase_flujo
        self.listar_beneficiarios_pase_flujo = listar_beneficiarios_pase_flujo
        self.revocar_beneficiario_pase_flujo = revocar_beneficiario_pase_flujo

    async def listar_catalogo(self) -> list[PaseCatalogoResult]:
        """
        Return the publishable catalogue of party passes.

        See ListarPasesFlujo._listar_pases for the full rules.
        """
        return await self.listar_pases_flujo._listar_pases()

    async def comprar_pases(
        self,
        responsable_id: str | None,
        pase_id: str,
        cantidad: int,
    ) -> PaseCompraCreadaResult:
        """
        Create a pass purchase (Compra + OrdenPago + CompraPase).

        See CrearCompraPaseFlujo._crear_compra_pase for the full rules.
        """
        return await self.crear_compra_pase_flujo._crear_compra_pase(
            responsable_id, pase_id, cantidad
        )

    async def obtener_compra(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseCompraDetalleResult:
        """
        Return the state of a pass purchase for its owner.

        See ObtenerCompraPaseFlujo._obtener_compra_pase for the full rules.
        """
        return await self.obtener_compra_pase_flujo._obtener_compra_pase(
            compra_id, responsable_id
        )

    async def listar_beneficiarios(
        self,
        compra_id: str,
        responsable_id: str | None,
    ) -> PaseBeneficiariosListaResult:
        """
        Return the beneficiaries of a pass batch with the slot accounting.

        See ListarBeneficiariosPaseFlujo._listar_beneficiarios for the rules.
        """
        return await self.listar_beneficiarios_pase_flujo._listar_beneficiarios(
            compra_id, responsable_id
        )

    async def asignar_beneficiarios(
        self,
        compra_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        beneficiario_ids: list[str],
    ) -> PaseBeneficiariosAsignadosResult:
        """
        Assign the persons of a paid pass batch to its free slots.

        See AsignarBeneficiariosPaseFlujo._asignar_beneficiarios for the rules.
        """
        return await self.asignar_beneficiarios_pase_flujo._asignar_beneficiarios(
            compra_id, responsable_id, actor_id, beneficiario_ids
        )

    async def revocar_beneficiario(
        self,
        compra_id: str,
        persona_id: str,
        responsable_id: str | None,
        actor_id: str | None,
        motivo: str,
    ) -> PaseBeneficiarioRevocadoResult:
        """
        Revoke a pass entitlement permanently.

        See RevocarBeneficiarioPaseFlujo._revocar_beneficiario for the rules.
        """
        return await self.revocar_beneficiario_pase_flujo._revocar_beneficiario(
            compra_id, persona_id, responsable_id, actor_id, motivo
        )
