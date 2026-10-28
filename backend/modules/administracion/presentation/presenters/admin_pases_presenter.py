"""
AdminPasesPresenter — pure transformer of the administrative cancellation of a
pass purchase.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps result objects
into the typed HTTP wrappers.
"""

from modules.administracion.domain.results.admin_pases_results import (
    AdminPaseCanceladaResult,
)
from modules.administracion.presentation.schemas.admin_pases_schemas import (
    AdminPaseCanceladaOut,
)


class AdminPasesPresenter:
    """Transformers of the administrative pass operations."""

    @staticmethod
    def present_cancelar_compra_pase(
        result: AdminPaseCanceladaResult,
    ) -> AdminPaseCanceladaOut:
        """Map the outcome of the cancellation into its HTTP wrapper."""
        return AdminPaseCanceladaOut(
            compra_id=result.compra_id,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            ya_cancelada=result.ya_cancelada,
            beneficiarios_revocados=result.beneficiarios_revocados,
            personas_afectadas=result.personas_afectadas,
            motivo=result.motivo,
        )


__all__ = ["AdminPasesPresenter"]
