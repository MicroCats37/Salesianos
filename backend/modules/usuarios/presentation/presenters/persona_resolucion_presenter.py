"""
PersonaResolucionPresenter — transforma el resultado de la resolución exacta
al schema HTTP.

Es un transformador PURO: no consulta la base de datos
(`contract/PLAN_REFACTORIZACION.md` §3.A).
"""

from modules.usuarios.domain.results import PersonaResueltaResult
from modules.usuarios.presentation.schemas.persona_resolucion_schemas import (
    PersonaResueltaOut,
)


class PersonaResolucionPresenter:
    """
    Transforma el resultado de dominio al wrapper HTTP.

    Patrón: Controller → Orchestrator → Presenter → HTTP Schema
    """

    @staticmethod
    def present_persona(result: PersonaResueltaResult) -> PersonaResueltaOut:
        """
        Transforma el resultado de la resolución al schema HTTP.

        Args:
            result: PersonaResueltaResult del orchestrator.

        Returns:
            PersonaResueltaOut para la respuesta HTTP.
        """
        return PersonaResueltaOut(
            persona_id=result.persona_id,
            nombre_completo=result.nombre_completo,
            tipo_documento=result.tipo_documento,
            numero_documento=result.numero_documento,
        )
