"""Inscripcion and InscripcionDelegado schemas for internal DTOs."""

from pydantic import BaseModel


class InscripcionCreateData(BaseModel):
    evento_id: str
    responsable_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: str | None = None
    observacion: str | None = None


class InscripcionUpdateEstadoData(BaseModel):
    estado: str
    observacion: str | None = None


class InscripcionResult(BaseModel):
    id: str
    evento_id: str
    responsable_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: str | None = None
    estado: str
    observacion: str | None

    class Config:
        from_attributes = True


class DelegadoCreateData(BaseModel):
    inscripcion_id: str
    persona_id: str


class DelegadoResult(BaseModel):
    id: str
    inscripcion_id: str
    persona_id: str

    class Config:
        from_attributes = True
