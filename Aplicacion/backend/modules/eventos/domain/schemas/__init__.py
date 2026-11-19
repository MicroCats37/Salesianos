"""Schemas internos (DTOs entre capas) del módulo `eventos`."""

from modules.eventos.domain.schemas.edicion_schemas import (
    EdicionCreateData,
    EdicionPublicarData,
    EdicionUpdateData,
)

__all__ = [
    "EdicionCreateData",
    "EdicionPublicarData",
    "EdicionUpdateData",
]
