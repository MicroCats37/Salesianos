"""
AdminFundacionPresenter — pure transformer of the foundation probe.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps a result
object into the typed HTTP wrapper.
"""

from modules.administracion.domain.results.admin_fundacion_results import (
    AdminFundacionResult,
)
from modules.administracion.presentation.schemas.admin_fundacion_schemas import (
    AdminHealthOut,
)


class AdminFundacionPresenter:
    """Transformers of the administration foundation."""

    @staticmethod
    def present_fundacion(result: AdminFundacionResult) -> AdminHealthOut:
        """Map the foundation result into its HTTP wrapper."""
        return AdminHealthOut(
            modulo=result.modulo,
            estado=result.estado,
            evento_activo_id=result.evento_activo_id,
            evento_activo_nombre=result.evento_activo_nombre,
        )


__all__ = ["AdminFundacionPresenter"]
