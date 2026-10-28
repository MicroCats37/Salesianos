"""
PersonaResolucionOrchestrator — fachada async ligera de la resolución exacta
de una identidad.

Sólo delega al flujo correspondiente; no contiene lógica de negocio
(`contract/django-app-architecture-contract.md` §4.5).
"""

from injector import inject

from modules.usuarios.domain.results import PersonaResueltaResult
from modules.usuarios.domain.services.flujos.persona_resolucion_flujo import (
    PersonaResolucionFlujo,
)


class PersonaResolucionOrchestrator:
    """
    Fachada async del resolver de identidad de una `Persona` registrada.
    """

    @inject
    def __init__(self, flujo: PersonaResolucionFlujo):
        self.flujo = flujo

    async def resolver_persona(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> PersonaResueltaResult:
        """
        Resuelve la `Persona` que corresponde EXACTAMENTE al documento.

        Args:
            tipo_documento: Tipo de documento (DNI, CE, PAS).
            numero_documento: Número de documento.

        Returns:
            PersonaResueltaResult con el id, el nombre y el documento.

        Raises:
            PersonaNoEncontradaError: no hay una `Persona` registrada con ese
                documento exacto.
        """
        return await self.flujo._proceso_resolver(tipo_documento, numero_documento)
