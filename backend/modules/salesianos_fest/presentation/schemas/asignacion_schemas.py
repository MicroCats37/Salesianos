"""
HTTP schemas for AsignacionCupo — Ninja/Schema request and response shapes.
"""
from pydantic import BaseModel, Field


# ── Asignar persona ───────────────────────────────────────────────────────────

class AsignarPersonaIn(BaseModel):
    """Input for assigning a person to an inscripcion."""
    inscripcion_id: str = Field(..., description="UUID of the Inscripcion")
    persona_id: str = Field(..., description="UUID of the Persona to assign")


class AsignarPersonaOut(BaseModel):
    """Output from assigning a person."""
    asignacion_id: str = Field(..., description="UUID of the created AsignacionCupo")
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    persona_id: str = Field(..., description="Persona UUID")
    estado: str = Field(..., description="Estado (ACTIVA)")
    compra_origen_id: str = Field(..., description="UUID of the Compra origen")


# ── Liberar cupo ─────────────────────────────────────────────────────────────

class LiberarCupoIn(BaseModel):
    """Input for liberating a player's cupo."""
    inscripcion_id: str = Field(..., description="UUID of the Inscripcion")
    persona_id: str = Field(..., description="UUID of the Persona to retire")
    motivo: str | None = Field(None, description="Reason for liberation")
    disciplina_id: str | None = Field(
        None,
        description=(
            "Optional. Scopes the release to ONE discipline: only the "
            "participations of that discipline are retired and the paid cup "
            "survives while the person keeps an active participation in "
            "another discipline. When omitted the release is inscripcion-scoped "
            "(every participation is retired and the cup is liberated)."
        ),
    )


class LiberarCupoOut(BaseModel):
    """Output from liberating a cupo."""
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    persona_id: str = Field(..., description="Persona UUID")
    asignacion_id: str | None = Field(None, description="AsignacionCupo UUID")
    estado: str = Field(..., description="New estado (LIBERADA or N/A)")
    cupo_liberado: bool = Field(
        ...,
        description=(
            "False when the cup survives because the person still holds an "
            "active participation in another discipline of the inscripcion."
        ),
    )


# ── Saldo ─────────────────────────────────────────────────────────────────────

class SaldoOut(BaseModel):
    """Output for saldo endpoint."""
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    contratados: int = Field(..., description="Total cupos contracted")
    pagados: int = Field(..., description="Total cupos paid")
    asignados_pagados: int = Field(..., description="Assigned paid cupos")
    disponibles_pagados: int = Field(..., description="Available paid cupos")


# ── Asignacion detail ─────────────────────────────────────────────────────────

class AsignacionDetailOut(BaseModel):
    """Output for AsignacionCupo detail."""
    id: str = Field(..., description="AsignacionCupo UUID")
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    compra_id: str = Field(..., description="Compra UUID")
    persona_id: str = Field(..., description="Persona UUID")
    persona_nombre: str = Field(..., description="Persona full name")
    estado: str = Field(..., description="Estado")
    motivo: str | None = Field(None, description="Motivo if LIBERADA/REVOCADA")
    liberada_en: str | None = Field(None, description="Liberation timestamp")
    created_at: str = Field(..., description="Creation timestamp")


class AsignacionListOut(BaseModel):
    """Output for listing AsignacionCupo."""
    asignaciones: list[AsignacionDetailOut] = Field(..., description="List of asignaciones")
