"""Equipo, ParticipacionDisciplina, and ParticipanteInscripcion schemas for internal DTOs."""

from pydantic import BaseModel


class EquipoCreateData(BaseModel):
    inscripcion_id: str
    disciplina_id: str
    categoria_id: str | None = None
    nombre: str


class EquipoUpdateData(BaseModel):
    nombre: str | None = None
    categoria_id: str | None = None


class EquipoResult(BaseModel):
    id: str
    inscripcion_id: str
    disciplina_id: str
    categoria_id: str | None = None
    nombre: str

    class Config:
        from_attributes = True


class ParticipacionCreateData(BaseModel):
    evento_id: str
    disciplina_id: str
    persona_id: str
    equipo_id: str


class ParticipacionResult(BaseModel):
    id: str
    evento_id: str
    disciplina_id: str
    persona_id: str
    equipo_id: str

    class Config:
        from_attributes = True


class ParticipanteCreateData(BaseModel):
    participacion_id: str
    equipo_id: str
    rol: str = "JUGADOR"
    talle_camiseta: str | None = None
    aseguradora_nombre: str | None = None
    aseguradora_numero_poliza: str | None = None
    notas: str | None = None


class ParticipanteUpdateData(BaseModel):
    rol: str | None = None
    talle_camiseta: str | None = None
    aseguradora_nombre: str | None = None
    aseguradora_numero_poliza: str | None = None
    notas: str | None = None
    # Note: aceptaciones is handled separately in the flujo to avoid
    # it being passed to ParticipanteInscripcion (which has no such field)


class ParticipanteResult(BaseModel):
    id: str
    participacion_id: str
    equipo_id: str
    rol: str
    talle_camiseta: str | None
    notas: str | None = None

    class Config:
        from_attributes = True
