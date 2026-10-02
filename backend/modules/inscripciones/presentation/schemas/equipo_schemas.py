"""HTTP schemas for Equipo, ParticipacionDisciplina, and ParticipanteInscripcion."""

from ninja import Schema
from pydantic import Field


class PersonaResumenOut(Schema):
    """Minimal persona info for nested responses."""

    id: str
    nombres: str
    apellidos: str
    numero_documento: str


class DisciplinaResumenOut(Schema):
    """Minimal discipline info for nested responses."""

    id: str
    nombre: str
    sigla: str


class CategoriaResumenOut(Schema):
    """Minimal category info for nested responses."""

    id: str
    nombre: str


class ParticipanteOut(Schema):
    """Participant response (role within a team)."""

    id: str
    participacion_id: str
    equipo_id: str
    rol: str
    talle_camiseta: str | None = None
    notas: str | None = None
    persona: PersonaResumenOut
    acepto_bases: bool = False
    acepto_aptitud_fisica: bool = False
    acepto_imagen: bool = False


class ParticipacionOut(Schema):
    """Participation response (person registered in a discipline)."""

    id: str
    evento_id: str
    disciplina_id: str
    persona_id: str
    equipo_id: str
    persona: PersonaResumenOut
    disciplina: DisciplinaResumenOut


class EquipoOut(Schema):
    """Basic team response."""

    id: str
    inscripcion_id: str
    disciplina_id: str
    categoria_id: str | None = None
    nombre: str


class EquipoDetalleOut(EquipoOut):
    """Detailed team response with participation data."""

    disciplina: DisciplinaResumenOut
    categoria: CategoriaResumenOut | None = None
    participantes: list[ParticipanteOut] = Field(default_factory=list)
