"""Disciplina and Categoria schemas for internal DTOs."""

from datetime import date
from pydantic import BaseModel


class DisciplinaCreateData(BaseModel):
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int | None = None
    max_jugadores: int | None = None
    esta_activa: bool = True


class DisciplinaUpdateData(BaseModel):
    nombre: str | None = None
    sigla: str | None = None
    modalidad: str | None = None
    min_jugadores: int | None = None
    max_jugadores: int | None = None
    esta_activa: bool | None = None


class DisciplinaResult(BaseModel):
    id: str
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int | None
    max_jugadores: int | None
    esta_activa: bool

    class Config:
        from_attributes = True


class CategoriaCreateData(BaseModel):
    disciplina_id: str
    nombre: str
    anio_minimo: int
    anio_maximo: int
    esta_activa: bool = True


class CategoriaUpdateData(BaseModel):
    nombre: str | None = None
    anio_minimo: int | None = None
    anio_maximo: int | None = None
    esta_activa: bool | None = None


class CategoriaResult(BaseModel):
    id: str
    disciplina_id: str
    nombre: str
    anio_minimo: int
    anio_maximo: int
    esta_activa: bool

    class Config:
        from_attributes = True
