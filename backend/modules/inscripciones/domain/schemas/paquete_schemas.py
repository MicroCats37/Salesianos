"""Paquete and PaqueteDisciplina schemas for internal DTOs."""

from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class PaqueteDisciplinaCreateData(BaseModel):
    paquete_id: str
    disciplina_id: str


class PaqueteCreateData(BaseModel):
    nombre: str
    descripcion: str | None = None
    cantidad_maxima_participantes: int
    precio_regular: Decimal
    precio_promocional: Decimal | None = None
    valido_desde: date
    valido_hasta: date
    esta_activo: bool = True
    modo_disciplinas: str = "ELEGIBLE"
    cantidad_disciplinas_requeridas: int | None = None


class PaqueteUpdateData(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    cantidad_maxima_participantes: int | None = None
    precio_regular: Decimal | None = None
    precio_promocional: Decimal | None = None
    valido_desde: date | None = None
    valido_hasta: date | None = None
    esta_activo: bool | None = None
    modo_disciplinas: str | None = None
    cantidad_disciplinas_requeridas: int | None = None


class PaqueteResult(BaseModel):
    id: str
    nombre: str
    descripcion: str | None
    cantidad_maxima_participantes: int
    precio_regular: Decimal
    precio_promocional: Decimal | None
    valido_desde: date
    valido_hasta: date
    esta_activo: bool
    modo_disciplinas: str
    cantidad_disciplinas_requeridas: int | None

    class Config:
        from_attributes = True
