"""HTTP schemas for Disciplina and Categoria."""

from ninja import Schema
from pydantic import Field


class DisciplinaOut(Schema):
    """Disciplina response schema."""

    id: str
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int | None = None
    max_jugadores: int | None = None
    esta_activa: bool


class CategoriaOut(Schema):
    """Categoria response schema."""

    id: str
    disciplina_id: str
    nombre: str
    anio_minimo: int
    anio_maximo: int
    esta_activa: bool


class DisciplinaDetalleOut(Schema):
    """Disciplina with its categories."""

    id: str
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int | None = None
    max_jugadores: int | None = None
    esta_activa: bool
    categorias: list[CategoriaOut] = Field(default_factory=list)
