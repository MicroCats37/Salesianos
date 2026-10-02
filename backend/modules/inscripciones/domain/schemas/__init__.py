"""Schemas package — internal Pydantic DTOs."""

from .disciplina_schemas import (
    DisciplinaCreateData,
    DisciplinaUpdateData,
    DisciplinaResult,
    CategoriaCreateData,
    CategoriaUpdateData,
    CategoriaResult,
)
from .paquete_schemas import (
    PaqueteCreateData,
    PaqueteUpdateData,
    PaqueteResult,
    PaqueteDisciplinaCreateData,
)
from .evento_schemas import (
    EventoCreateData,
    EventoUpdateData,
    EventoResult,
)
from .inscripcion_schemas import (
    InscripcionCreateData,
    InscripcionUpdateEstadoData,
    InscripcionResult,
    DelegadoCreateData,
    DelegadoResult,
)
from .equipo_schemas import (
    EquipoCreateData,
    EquipoUpdateData,
    EquipoResult,
    ParticipacionCreateData,
    ParticipacionResult,
    ParticipanteCreateData,
    ParticipanteUpdateData,
    ParticipanteResult,
)
