"""
Internal DTOs for AsignacionCupo domain operations.
"""
from pydantic import BaseModel


class AsignacionCupoCreateData(BaseModel):
    """Data needed to create an AsignacionCupo."""
    inscripcion_id: str
    inscripcion_persona_id: str


class AsignacionCupoResult(BaseModel):
    """Result of an AsignacionCupo operation."""
    asignacion_id: str
    inscripcion_id: str
    persona_id: str
    estado: str
    compra_origen_id: str | None = None


class SaldoInscripcionResult(BaseModel):
    """Saldo de cupos de una inscripcion."""
    inscripcion_id: str
    contratados: int
    pagados: int
    asignados_pagados: int
    disponibles_pagados: int
