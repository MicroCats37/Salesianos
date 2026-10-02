"""
PersonaBusquedaPresenter — transforma resultados de consulta externa a esquemas HTTP.

Reutiliza ConsultaDocumentoResult de entidades y lo transforma al schema HTTP.
"""

from modules.usuarios.domain.results import ConsultaDocumentoResult
from modules.usuarios.presentation.schemas.persona_busqueda_schemas import DocumentoConsultaOut


class PersonaBusquedaPresenter:
    """
    Transforma objetos de resultado de consulta externa a esquemas de respuesta HTTP.

    Patrón: Controller → Orchestrator → Presenter → HTTP Schema
    """

    @staticmethod
    def present_documento(result: ConsultaDocumentoResult) -> DocumentoConsultaOut:
        """
        Transforma el resultado unificado de consulta a esquema HTTP minimal.

        Args:
            result: ConsultaDocumentoResult del orchestrator

        Returns:
            DocumentoConsultaOut schema para respuesta HTTP
        """
        return DocumentoConsultaOut(
            tipo_documento=result.tipo_documento,
            numero_documento=result.numero_documento,
            razon_social=result.razon_social,
        )
