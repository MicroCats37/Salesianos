"""Presentation schemas for the inscripciones module."""

from modules.inscripciones.presentation.schemas.disciplina_schemas import (
    DisciplinaOut,
    CategoriaOut,
    DisciplinaDetalleOut,
)
from modules.inscripciones.presentation.schemas.paquete_schemas import (
    PaqueteOut,
    PaqueteDetalleOut,
    PaqueteDisciplinaOut,
)
from modules.inscripciones.presentation.schemas.evento_schemas import (
    EventoOut,
)
from modules.inscripciones.presentation.schemas.promocion_schemas import (
    PromocionOut,
)
from modules.inscripciones.presentation.schemas.inscripcion_schemas import (
    AgregarParticipanteOut,
    AgregarParticipantesOut,
    InscripcionCreateIn,
    InscripcionOut,
    InscripcionDetalleOut,
    CambiarEstadoIn,
    AsignarDelegadoIn,
    DelegadoOut,
    EventoResumenOut,
    PaqueteResumenOut,
    PromocionResumenOut,
)
from modules.inscripciones.presentation.schemas.equipo_schemas import (
    EquipoOut,
    EquipoDetalleOut,
    ParticipacionOut,
    ParticipanteOut,
    PersonaResumenOut,
    DisciplinaResumenOut,
    CategoriaResumenOut,
)
from modules.inscripciones.presentation.schemas.inscripcion_schemas import (
    ParticipanteCreateIn,
    EquipoCreateIn,
)
