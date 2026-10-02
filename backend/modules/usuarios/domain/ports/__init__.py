"""Domain ports for usuarios external integrations."""

from abc import ABC, abstractmethod

from modules.usuarios.domain.results import ConsultaDocumentoResult


class IConsultaExternaClient(ABC):
    """Puerto unificado para consulta de documento por número (DNI o RUC)."""

    @abstractmethod
    async def consultar_documento(self, documento: str) -> ConsultaDocumentoResult:
        """Obtiene datos por DNI (8 dígitos) o RUC (11 dígitos)."""
        ...


__all__ = ["IConsultaExternaClient"]
