"""Re-export de los DTOs internos del módulo."""

from .persona_schemas import (
    PersonaConfirmarData,
    PersonaCreateData,
    normalizar_numero_documento,
    normalizar_tipo_documento,
)

__all__ = [
    "PersonaConfirmarData",
    "PersonaCreateData",
    "normalizar_numero_documento",
    "normalizar_tipo_documento",
]
