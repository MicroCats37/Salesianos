"""
HTTP schemas of the competencias module — the request/response contract.

Every schema inherits from `BaseSchema` (`contract/PLAN_REFACTORIZACION.md`
§C) and the schemas are COMPOSED from blocks instead of being duplicated
endpoint by endpoint (`contract/SCHEMA_DRY_INTENTION.md`):

- the IDENTITY block carries the identifiers,
- the GENERAL block carries the data every read of the entity shares,
- the endpoint schema adds only what is specific to that endpoint.

The schemas are the MIRROR of the frontend schemas (Phase 4): a field added
here must be added there too.

The motive of a protected mutation is OPTIONAL in the HTTP schema on
purpose: the rule (5..500 characters) belongs to the DOMAIN, which publishes
the stable code `REASON_REQUIRED`. Duplicating the rule here would replace
that code with a generic validation error
(`contract/django-app-architecture-contract.md` §10 — "no duplicar
validación").
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


# ── Bloque identidad ─────────────────────────────────────────────────────────


class CompetenciaIdentidadOut(BaseSchema):
    """Identifiers of a competition."""

    id: UUID
    evento_id: UUID
    disciplina_id: UUID
    categoria_id: UUID


class CompetenciaGeneralOut(BaseSchema):
    """Data every read of a competition shares."""

    nombre: str
    fecha: date
    estado: str


# ── Lecturas ────────────────────────────────────────────────────────────────


class CompetenciaListOut(CompetenciaIdentidadOut, CompetenciaGeneralOut):
    """Row of the list of competitions."""

    version: int
    total_equipos: int
    total_encuentros: int
    total_encuentros_finalizados: int


class CompetenciaEquipoOut(BaseSchema):
    """Participation of a team inside the bracket."""

    id: UUID
    competencia_id: UUID
    equipo_id: UUID
    equipo_nombre: str
    orden: int
    estado: str
    version: int


class RondaOut(BaseSchema):
    """Round of the bracket."""

    id: UUID
    competencia_id: UUID
    etiqueta: str
    orden: int
    estado: str
    version: int
    total_encuentros: int


class CompetenciaDetalleOut(CompetenciaListOut):
    """Detail of a competition: its teams and its rounds."""

    created_at: datetime
    equipos: list[CompetenciaEquipoOut]
    rondas: list[RondaOut]


class EncuentroOut(BaseSchema):
    """Encounter of the bracket."""

    id: UUID
    ronda_id: UUID
    ronda_etiqueta: str | None = None
    ronda_orden: int | None = None
    competencia_id: UUID | None = None
    competencia_nombre: str | None = None
    orden: int
    participante_1_id: UUID | None = None
    participante_1_nombre: str | None = None
    participante_2_id: UUID | None = None
    participante_2_nombre: str | None = None
    inicio_programado: datetime | None = None
    fin_programado: datetime | None = None
    estado: str
    estado_pre_suspension: str | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    es_bye: bool
    ganador_id: UUID | None = None
    puntaje_1: int | None = None
    puntaje_2: int | None = None
    marcador_detalle: str
    siguiente_encuentro_id: UUID | None = None
    slot_destino: str | None = None
    ganador_propagado_id: UUID | None = None
    version: int


class RondaCuadroOut(BaseSchema):
    """Column of the bracket: a round and its encounters."""

    id: UUID
    etiqueta: str
    orden: int
    estado: str
    encuentros: list[EncuentroOut]


class CuadroOut(BaseSchema):
    """Bracket of a competition (it may be empty or partial)."""

    competencia_id: UUID
    nombre: str
    fecha: date
    estado: str
    total_equipos: int
    rondas: list[RondaCuadroOut]


class AgendaOut(BaseSchema):
    """Agenda of ONE day."""

    fecha: date
    total: int
    encuentros: list[EncuentroOut]


# ── Comandos (respuestas) ───────────────────────────────────────────────────


class AvancePreviewOut(BaseSchema):
    """Proposal of the propagation of the winner (it never writes)."""

    encuentro_id: UUID
    siguiente_encuentro_id: UUID
    slot_destino: str
    ganador_id: UUID
    ocupante_actual_id: UUID | None = None
    ya_propagado: bool
    bloqueado: bool
    motivo_bloqueo: str | None = None


class AvanceOut(BaseSchema):
    """Outcome of the propagation of the winner."""

    encuentro_origen_id: UUID
    siguiente_encuentro_id: UUID
    slot_destino: str
    ganador_id: UUID
    ya_aplicado: bool
    destino: EncuentroOut


class ImpactoDescendienteOut(BaseSchema):
    """Impact of a correction over ONE descendant of the link."""

    encuentro_id: UUID
    slot: str
    estado: str
    ocupante_actual_id: UUID | None = None
    ganador_propagado_id: UUID | None = None
    bloqueado: bool
    motivo_bloqueo: str | None = None
    se_reemplaza: bool
    se_limpia_resultado: bool


class CorreccionPreviewOut(BaseSchema):
    """Impact analysis of the correction of the winner."""

    encuentro_id: UUID
    ganador_actual_id: UUID | None = None
    ganador_nuevo_id: UUID
    requiere_override: bool
    descendientes: list[ImpactoDescendienteOut]


class CorreccionOut(BaseSchema):
    """Outcome of the correction of the winner."""

    encuentro_id: UUID
    ganador_id: UUID
    requirio_override: bool
    descendientes_afectados: int
    encuentro: EncuentroOut
    descendientes: list[ImpactoDescendienteOut]


# ── Comandos (entradas) ─────────────────────────────────────────────────────


class CompetenciaCreateIn(BaseSchema):
    """Data needed to create a competition."""

    evento_id: UUID
    disciplina_id: UUID
    categoria_id: UUID
    nombre: str = Field(min_length=1, max_length=150)
    fecha: date


class CompetenciaUpdateIn(BaseSchema):
    """Editable fields of a competition."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    fecha: date | None = None
    expected_version: int = Field(ge=1)


class CompetenciaEstadoIn(BaseSchema):
    """New lifecycle state of a competition."""

    estado: str = Field(min_length=1, max_length=20)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class CompetenciaEquipoCreateIn(BaseSchema):
    """Team to register in the bracket, with its MANUAL order."""

    equipo_id: UUID
    orden: int = Field(ge=1)


class CompetenciaEquipoUpdateIn(BaseSchema):
    """Editable fields of the participation of a team."""

    orden: int | None = Field(default=None, ge=1)
    estado: str | None = Field(default=None, min_length=1, max_length=20)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class RondaCreateIn(BaseSchema):
    """Round to create in the bracket."""

    etiqueta: str = Field(min_length=1, max_length=100)
    orden: int = Field(ge=1)


class RondaUpdateIn(BaseSchema):
    """Editable fields of a round."""

    etiqueta: str | None = Field(default=None, min_length=1, max_length=100)
    orden: int | None = Field(default=None, ge=1)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class RondaEstadoIn(BaseSchema):
    """New state of a round (it is invalidated, never deleted)."""

    estado: str = Field(min_length=1, max_length=20)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class EncuentroCreateIn(BaseSchema):
    """Encounter to create in a round of the bracket.

    Both participants are optional ON PURPOSE: an empty or partial bracket
    must be readable and editable without inventing participants.
    """

    ronda_id: UUID
    orden: int = Field(ge=1)
    participante_1_id: UUID | None = None
    participante_2_id: UUID | None = None


class EncuentroParticipantesIn(BaseSchema):
    """Teams of the two slots of an encounter (moving a slot needs a motive)."""

    participante_1_id: UUID | None = None
    participante_2_id: UUID | None = None
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class EncuentroProgramacionIn(BaseSchema):
    """Schedule of an encounter — a positive interval of the competition day."""

    inicio_programado: datetime
    fin_programado: datetime
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class EncuentroEstadoIn(BaseSchema):
    """New lifecycle state of an encounter."""

    estado: str = Field(min_length=1, max_length=20)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class EncuentroEnlaceIn(BaseSchema):
    """Link of an encounter to the next encounter of the bracket."""

    siguiente_encuentro_id: UUID
    slot_destino: str = Field(min_length=1, max_length=20)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class EncuentroDesenlaceIn(BaseSchema):
    """Removal of the link of an encounter (it needs an audited motive)."""

    motivo: str | None = None
    expected_version: int = Field(ge=1)


class ResultadoEncuentroIn(BaseSchema):
    """Authoritative result of an encounter.

    The winner is AUTHORITATIVE: it must occupy one of the two slots. The
    scores are optional and purely informative — they never determine nor
    contradict the winner.
    """

    ganador_id: UUID
    puntaje_1: int | None = Field(default=None, ge=0)
    puntaje_2: int | None = Field(default=None, ge=0)
    marcador_detalle: str | None = Field(default=None, max_length=500)
    motivo: str | None = None
    expected_version: int = Field(ge=1)


class AvanceConfirmarIn(BaseSchema):
    """Confirmation of the propagation of the winner."""

    motivo: str | None = None
    expected_version: int = Field(ge=1)


class CorreccionPreviewIn(BaseSchema):
    """Winner proposed for the correction (the preview never writes)."""

    ganador_id: UUID


class CorreccionConfirmarIn(BaseSchema):
    """Confirmation of the correction of the authoritative winner.

    `override` and `acepta_impacto` are only honoured when a descendant of
    the link already started, finished or was cancelled: without them the
    correction changes NOTHING (never a silent cascade).
    """

    ganador_id: UUID
    motivo: str | None = None
    override: bool = False
    acepta_impacto: bool = False
    expected_version: int = Field(ge=1)


__all__ = [
    "AgendaOut",
    "AvanceConfirmarIn",
    "AvanceOut",
    "AvancePreviewOut",
    "CompetenciaCreateIn",
    "CompetenciaDetalleOut",
    "CompetenciaEquipoCreateIn",
    "CompetenciaEquipoOut",
    "CompetenciaEquipoUpdateIn",
    "CompetenciaEstadoIn",
    "CompetenciaGeneralOut",
    "CompetenciaIdentidadOut",
    "CompetenciaListOut",
    "CompetenciaUpdateIn",
    "CorreccionConfirmarIn",
    "CorreccionOut",
    "CorreccionPreviewIn",
    "CorreccionPreviewOut",
    "CuadroOut",
    "EncuentroCreateIn",
    "EncuentroDesenlaceIn",
    "EncuentroEnlaceIn",
    "EncuentroEstadoIn",
    "EncuentroOut",
    "EncuentroParticipantesIn",
    "EncuentroProgramacionIn",
    "ImpactoDescendienteOut",
    "ResultadoEncuentroIn",
    "RondaCreateIn",
    "RondaCuadroOut",
    "RondaEstadoIn",
    "RondaOut",
    "RondaUpdateIn",
]
