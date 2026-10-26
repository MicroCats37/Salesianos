"""
Result DTOs for AsignacionCupo operations — returned by services to orchestrators.
"""
from dataclasses import dataclass


@dataclass
class AsignacionCupoCreatedResult:
    """Result of creating an AsignacionCupo."""
    asignacion_id: str
    inscripcion_id: str
    persona_id: str
    estado: str
    compra_origen_id: str | None = None


@dataclass
class AsignacionCupoLiberadaResult:
    """Result of liberating an AsignacionCupo."""
    asignacion_id: str
    inscripcion_id: str
    persona_id: str
    estado: str
