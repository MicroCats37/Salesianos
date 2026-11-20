"""Re-export de los resultados de dominio."""

from .auth_result_schemas import LoginTokenResult, SesionUsuarioResult
from .persona_resolucion_results import (
    ConsultaDocumentoResultado,
    PersonaDatosExternos,
    PersonaResolucionResult,
)

__all__ = [
    "ConsultaDocumentoResultado",
    "LoginTokenResult",
    "PersonaDatosExternos",
    "PersonaResolucionResult",
    "SesionUsuarioResult",
]
