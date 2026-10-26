"""Internal DTOs of the competencias module — NOT HTTP schemas.

These are the contracts exchanged between the orchestrators, the flows and
the core services (contract/django-app-architecture-contract.md §4.6). The
HTTP schemas of the module live in `presentation/schemas/` (Phase 3).
"""
from datetime import date, datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class CompetenciaCreateData(PydanticBaseModel):
    """Data needed to create a competition."""

    evento_id: str
    disciplina_id: str
    categoria_id: str
    nombre: str
    fecha: date


class CompetenciaUpdateData(PydanticBaseModel):
    """Editable fields of a competition (its identity and its date)."""

    nombre: str | None = None
    fecha: date | None = None


class CompetenciaEquipoCreateData(PydanticBaseModel):
    """Data needed to register a team inside the bracket."""

    equipo_id: str
    orden: int


class CompetenciaEquipoUpdateData(PydanticBaseModel):
    """Editable fields of the participation of a team."""

    orden: int | None = None
    estado: str | None = None


class RondaCreateData(PydanticBaseModel):
    """Data needed to create a round of the bracket."""

    etiqueta: str
    orden: int


class RondaUpdateData(PydanticBaseModel):
    """Editable fields of a round."""

    etiqueta: str | None = None
    orden: int | None = None


class EncuentroCreateData(PydanticBaseModel):
    """Data needed to create an encounter.

    Both participants are optional on purpose: an empty or partial bracket
    must be readable and editable without inventing participants.
    """

    orden: int
    participante_1_id: str | None = None
    participante_2_id: str | None = None


class EncuentroParticipantesData(PydanticBaseModel):
    """Participants of an encounter (either slot may stay empty)."""

    participante_1_id: str | None = None
    participante_2_id: str | None = None


class EncuentroProgramacionData(PydanticBaseModel):
    """Schedule of an encounter — a positive interval of the competition day."""

    inicio_programado: datetime
    fin_programado: datetime


class EncuentroEnlaceData(PydanticBaseModel):
    """Link of an encounter to the next encounter of the bracket.

    The link and its destination slot always travel together (model
    constraint `ck_encuentro_enlace_slot`): one without the other is
    meaningless.
    """

    siguiente_encuentro_id: str
    slot_destino: str


class ResultadoEncuentroData(PydanticBaseModel):
    """Authoritative result of an encounter.

    The winner is AUTHORITATIVE and it MUST occupy one of the two slots.
    The scores are optional and purely informative: they never determine nor
    contradict the winner (design: "los puntajes no infieren ni validan al
    ganador autoritativo").
    """

    ganador_id: str
    puntaje_1: int | None = Field(default=None, ge=0)
    puntaje_2: int | None = Field(default=None, ge=0)
    marcador_detalle: str = Field(default="", max_length=500)


class CorreccionGanadorData(PydanticBaseModel):
    """Correction of the authoritative winner of an encounter.

    `override` and `acepta_impacto` are only honoured when a descendant of
    the link already started, finished or was cancelled: without them the
    correction changes NOTHING (never a silent cascade).
    """

    ganador_id: str
    motivo: str
    override: bool = False
    acepta_impacto: bool = False


class CompetenciaFiltrosData(PydanticBaseModel):
    """Filters of the read surfaces of the competitions.

    The filters combine with AND. They are an INTERNAL DTO: the HTTP layer
    maps the query parameters onto it, so the selectors never receive a raw
    dict and never parse strings.
    """

    evento_id: str | None = None
    disciplina_id: str | None = None
    categoria_id: str | None = None
    estado: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None


class EncuentroFiltrosData(PydanticBaseModel):
    """Filters of the read surfaces of the encounters (bracket and agenda)."""

    evento_id: str | None = None
    competencia_id: str | None = None
    ronda_id: str | None = None
    disciplina_id: str | None = None
    categoria_id: str | None = None
    estado: str | None = None
    fecha: date | None = None
