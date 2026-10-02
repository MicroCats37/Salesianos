"""
PersonaBusquedaOrchestrator — fachada asíncrona ligera para consulta de personas.

Reutiliza el flujo PersonaBusquedaFlujo que delega a IConsultaExternaClient.
"""

from injector import inject

from modules.usuarios.domain.results import ConsultaDocumentoResult
from modules.usuarios.domain.services.flujos.persona_busqueda_flujo import PersonaBusquedaFlujo


class PersonaBusquedaOrchestrator:
    """
    Fachada asíncrona ligera para consulta de personas por documento.

    Solo delega al flujo correspondiente; no contiene lógica de negocio.
    """

    @inject
    def __init__(
        self,
        busqueda_flujo: PersonaBusquedaFlujo,
    ):
        self.busqueda_flujo = busqueda_flujo

    async def buscar_documento(self, documento: str) -> ConsultaDocumentoResult:
        """
        Consulta datos de documento por número (DNI o RUC).

        Auto-detecta: 8 dígitos → DNI (RENIEC), 11 dígitos → RUC (SUNAT).

        Args:
            documento: Número de documento (8 o 11 dígitos).

        Returns:
            ConsultaDocumentoResult con tipo_documento, numero_documento, razon_social.

        Raises:
            SunatNotFoundError: Si el RUC (11 dígitos) no existe.
            ReniecNotFoundError: Si el DNI (8 dígitos) no existe.
        """
        return await self.busqueda_flujo._proceso_busqueda(documento)
