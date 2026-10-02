"""Evento schemas for internal DTOs."""

from datetime import date
from pydantic import BaseModel


class EventoCreateData(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    esta_activo: bool = True


class EventoUpdateData(BaseModel):
    nombre: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    esta_activo: bool | None = None


class EventoResult(BaseModel):
    id: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    esta_activo: bool

    class Config:
        from_attributes = True
