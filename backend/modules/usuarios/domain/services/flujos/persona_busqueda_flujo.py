"""
PersonaBusquedaFlujo — flujo async para consulta de personas por documento (RENIEC/SUNAT).

Reutiliza IConsultaExternaClient de entidades para no duplicar infraestructura.
"""

from injector import inject

from modules.usuarios.domain.ports import IConsultaExternaClient
from modules.usuarios.domain.results import ConsultaDocumentoResult


class PersonaBusquedaFlujo:
    """
    Flujo async para consulta de documento por número (DNI o RUC).

    Auto-detecta el tipo por longitud: 8=DNI, 11=RUC.
    """

    @inject
    def __init__(self, consulta_cliente: IConsultaExternaClient):
        self.consulta_cliente = consulta_cliente

    async def _proceso_busqueda(self, documento: str) -> ConsultaDocumentoResult:
        """
        Proceso para consultar datos de documento por número.

        Args:
            documento: Número de documento (8 o 11 dígitos).

        Returns:
            ConsultaDocumentoResult con tipo_documento, numero_documento, razon_social.

        Raises:
            SunatNotFoundError: Si el RUC (11 dígitos) no existe.
            ReniecNotFoundError: Si el DNI (8 dígitos) no existe.
        """
        return await self.consulta_cliente.consultar_documento(documento)
