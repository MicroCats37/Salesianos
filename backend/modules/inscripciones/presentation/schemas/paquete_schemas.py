"""HTTP schemas for Paquete."""

from datetime import date
from decimal import Decimal

from ninja import Schema
from pydantic import Field


class PaqueteDisciplinaOut(Schema):
    """PaqueteDisciplina response (discipline inside a package)."""

    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    min_jugadores: int | None = None
    max_jugadores: int | None = None


class PaqueteOut(Schema):
    """Paquete response schema."""

    id: str
    nombre: str
    descripcion: str | None = None
    cantidad_maxima_participantes: int
    precio_regular: float
    precio_promocional: float | None = None
    valido_desde: date
    valido_hasta: date
    esta_activo: bool
    modo_disciplinas: str
    cantidad_disciplinas_requeridas: int | None = None
    cantidad_maxima_equipos: int
    disciplinas: list[PaqueteDisciplinaOut] = Field(default_factory=list)


class PaqueteDetalleOut(PaqueteOut):
    """Paquete with its disciplines."""
