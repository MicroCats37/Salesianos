"""Re-export de los DTOs internos del módulo `salesianos_fest`."""

from modules.salesianos_fest.domain.schemas.catalogo_schemas import (
    DisciplinaOfertaData,
    PaqueteOfertaData,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    CompraCuposData,
    ParticipanteAsignarData,
)

__all__ = [
    "CompraCuposData",
    "DisciplinaOfertaData",
    "EquipoCreateData",
    "InscripcionInicialData",
    "PaqueteOfertaData",
    "ParticipanteAsignarData",
]
