"""
HTTP wrappers of the registrations, teams and participants (A3, A4, A7, A8, A9).

The blocks are COMPOSED, never duplicated (`contract/SCHEMA_DRY_INTENTION.md`):
the team block and the participant block are shared by the list and the
drilldown endpoints, and the drilldown wrapper INHERITS the list wrapper
instead of repeating its fields.

Every wrapper is explicit: no generic `data` / `contexto` envelope
(`contract/api-wrapper-presenter-contract.md` §5).
"""
from datetime import date, datetime
from typing import Optional

from core.types import BaseSchema
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminPagoListItemOut,
)


class AdminEquipoListItemOut(BaseSchema):
    """A team with its roster completeness."""

    id: str
    nombre: str
    disciplina_sigla: str
    disciplina_nombre: str
    categoria_nombre: Optional[str] = None
    inscripcion_id: str
    inscripcion_ref: str
    estado: str
    jugadores_registrados: int
    minimo_deportivo: int
    faltantes: int
    estado_roster: str
    created_at: datetime


class AdminParticipacionListItemOut(BaseSchema):
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


class AdminEquipoDetalleOut(AdminEquipoListItemOut):
    """A team with its roster rows (the drilldown of A4)."""

    participaciones: list[AdminParticipacionListItemOut] = []


class AdminParticipanteListItemOut(BaseSchema):
    """A registered person and their pool eligibility."""

    inscripcion_persona_id: str
    persona_id: str
    persona_nombre: str
    persona_documento: str
    inscripcion_id: str
    estado: str
    estado_pool: str
    motivo_bloqueo: Optional[str] = None
    tiene_cupo_activo: bool
    disciplinas: list[str] = []
    created_at: datetime


class AdminAsignacionListItemOut(BaseSchema):
    """A cup assignment: the link between a paid cup and a person."""

    id: str
    persona_nombre: str
    estado: str
    motivo: Optional[str] = None
    liberada_en: Optional[datetime] = None
    compra_id: str
    created_at: datetime


class AdminAceptacionListItemOut(BaseSchema):
    """A legal acceptance given by a person of the registration."""

    persona_id: str
    tipo_aceptacion: str
    documento_version: str
    aceptado_en: datetime
    medio: str


class AdminSaldoOut(BaseSchema):
    """The cup balance of a registration."""

    contratados: int
    pagados: int
    asignados_pagados: int
    disponibles_pagados: int


class AdminInscripcionListItemOut(BaseSchema):
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


class AdminInscripcionDetailOut(AdminInscripcionListItemOut):
    """The drilldown of a registration (A4)."""

    delegado_nombre: Optional[str] = None
    observacion: str = ""
    fecha_limite_modificacion: Optional[date] = None
    equipos: list[AdminEquipoDetalleOut] = []
    participantes: list[AdminParticipanteListItemOut] = []
    compras: list[AdminPagoListItemOut] = []
    asignaciones: list[AdminAsignacionListItemOut] = []
    aceptaciones: list[AdminAceptacionListItemOut] = []
    saldo: AdminSaldoOut


__all__ = [
    "AdminEquipoListItemOut",
    "AdminEquipoDetalleOut",
    "AdminParticipacionListItemOut",
    "AdminParticipanteListItemOut",
    "AdminAsignacionListItemOut",
    "AdminAceptacionListItemOut",
    "AdminSaldoOut",
    "AdminInscripcionListItemOut",
    "AdminInscripcionDetailOut",
]
