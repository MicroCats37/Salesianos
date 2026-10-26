"""
Results for the paid-cup repair flow (RepararCuposFlujo).

Internal DTOs — they never reach the HTTP layer. The management command is the
only consumer and it prints them.
"""
from typing import Optional

from pydantic import BaseModel

from modules.salesianos_fest.domain.constants import EstadoReparacionCupoChoices


class RepararCuposInscripcionResult(BaseModel):
    """Outcome of the repair of a single inscripcion."""

    inscripcion_id: str
    # Paid capacity of the inscripcion.
    pagados: int
    # Paid capacity already consumed by an ACTIVA AsignacionCupo.
    asignados_pagados: int
    # Paid capacity still free.
    disponibles_pagados: int
    # ACTIVO preregistrations still waiting for a paid cup.
    pendientes: int
    # Assignments created by this run (0 in a dry run).
    asignaciones_creadas: int
    estado: str = EstadoReparacionCupoChoices.SIN_PENDIENTES
    # Technical detail of a failure — never shown to the end user.
    motivo: Optional[str] = None


class RepararCuposResult(BaseModel):
    """Summary of a repair run."""

    dry_run: bool
    # Inscripciones reviewed.
    revisadas: int = 0
    # Inscripciones that materialized at least one cup.
    reparadas: int = 0
    # Inscripciones without participants waiting for a cup.
    sin_pendientes: int = 0
    # Inscripciones that failed.
    errores: int = 0
    # Total assignments created by this run.
    asignaciones_creadas: int = 0
    detalle: list[RepararCuposInscripcionResult] = []
