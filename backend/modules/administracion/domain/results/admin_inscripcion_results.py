"""
Result DTOs of the registrations, teams and participants (A3, A4, A7, A8, A9).

These are the internal hand-off between the domain services and the
presenters. Every DERIVED number is computed in the backend: the frontend
never re-derives a count, a balance or an eligibility
(`contract/api-wrapper-presenter-contract.md` §7).

The blocks are shared: the team block and the participant block are reused by
the registration detail (A4), the team list (A7) and the participant lists
(A8/A9), so the same data is never described twice
(`contract/SCHEMA_DRY_INTENTION.md`).
"""

from datetime import date, datetime

from pydantic import BaseModel

from modules.administracion.domain.results.admin_pago_results import (
    AdminPagoListItemResult,
)


class AdminParticipacionListItemResult(BaseModel):
    """A roster row: one person placed in one team of one discipline."""

    id: str
    inscripcion_persona_id: str
    persona_nombre: str
    persona_documento: str
    equipo_nombre: str
    disciplina_sigla: str
    inscripcion_id: str
    rol: str
    talla_camiseta: str
    estado: str
    created_at: datetime


class AdminEquipoListItemResult(BaseModel):
    """A team with its roster completeness."""

    id: str
    nombre: str
    disciplina_sigla: str
    disciplina_nombre: str
    categoria_nombre: str | None = None
    inscripcion_id: str
    inscripcion_ref: str
    estado: str
    jugadores_registrados: int
    minimo_deportivo: int
    faltantes: int
    estado_roster: str
    created_at: datetime


class AdminEquipoDetalleResult(AdminEquipoListItemResult):
    """A team with its roster rows (the drilldown of A4)."""

    participaciones: list[AdminParticipacionListItemResult] = []


class AdminParticipanteListItemResult(BaseModel):
    """A registered person and their pool eligibility."""

    inscripcion_persona_id: str
    persona_id: str
    persona_nombre: str
    persona_documento: str
    inscripcion_id: str
    estado: str
    estado_pool: str
    motivo_bloqueo: str | None = None
    tiene_cupo_activo: bool
    disciplinas: list[str] = []
    created_at: datetime


class AdminAsignacionListItemResult(BaseModel):
    """A cup assignment: the link between a paid cup and a person."""

    id: str
    persona_nombre: str
    estado: str
    motivo: str | None = None
    liberada_en: datetime | None = None
    compra_id: str
    created_at: datetime


class AdminAceptacionListItemResult(BaseModel):
    """A legal acceptance given by a person of the registration."""

    persona_id: str
    tipo_aceptacion: str
    documento_version: str
    aceptado_en: datetime
    medio: str


class AdminSaldoResult(BaseModel):
    """The cup balance of a registration.

    The numbers are the ones of
    `AsignacionCoreService.calcular_saldo_inscripcion()`: contracted, paid,
    assigned (from paid purchases) and still free.
    """

    contratados: int
    pagados: int
    asignados_pagados: int
    disponibles_pagados: int


class AdminInscripcionListItemResult(BaseModel):
    """A registration with its operational counters."""

    id: str
    evento_nombre: str
    responsable_nombre: str
    responsable_documento: str
    paquete_nombre: str
    promocion_nombre: str
    estado: str
    equipos_total: int
    equipos_completos: int
    personas: int
    participaciones: int
    cupos_contratados: int
    cupos_pagados: int
    cupos_disponibles: int
    monto_pagado: float
    created_at: datetime


class AdminInscripcionDetalleResult(AdminInscripcionListItemResult):
    """The drilldown of a registration (A4)."""

    delegado_nombre: str | None = None
    observacion: str = ""
    fecha_limite_modificacion: date | None = None
    equipos: list[AdminEquipoDetalleResult] = []
    participantes: list[AdminParticipanteListItemResult] = []
    compras: list[AdminPagoListItemResult] = []
    asignaciones: list[AdminAsignacionListItemResult] = []
    aceptaciones: list[AdminAceptacionListItemResult] = []
    saldo: AdminSaldoResult


__all__ = [
    "AdminEquipoListItemResult",
    "AdminEquipoDetalleResult",
    "AdminParticipanteListItemResult",
    "AdminParticipacionListItemResult",
    "AdminAsignacionListItemResult",
    "AdminAceptacionListItemResult",
    "AdminSaldoResult",
    "AdminInscripcionListItemResult",
    "AdminInscripcionDetalleResult",
]
