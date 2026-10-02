"""Consulta results - DTO unificado para consulta de documentos (DNI/RUC)."""

from dataclasses import dataclass


@dataclass
class ConsultaDocumentoResult:
    """Resultado unificado de consulta por número de documento."""

    tipo_documento: str
    numero_documento: str
    razon_social: str
