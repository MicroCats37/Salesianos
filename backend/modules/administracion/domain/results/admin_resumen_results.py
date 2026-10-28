"""
AdminResumenResult — internal DTOs of the operational overview (A1).

The presenters transform result objects into HTTP schemas; they never touch
the ORM (`contract/api-wrapper-presenter-contract.md` §3). These DTOs are the
hand-off between the orchestrator and the presenter.

Every metric is computed HERE, in the backend: the frontend never re-derives
a count, a balance or an eligibility (`contract/api-wrapper-presenter-contract.md` §7).
"""

from datetime import date, datetime

from pydantic import BaseModel


class EventoResumenResult(BaseModel):
    """Identity and calendar of the active event."""

    id: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    esta_activo: bool
    fecha_limite_modificacion: date | None = None
    puede_modificar: bool


class AdminInscripcionesResumenResult(BaseModel):
    """Administrative state of the registrations — never the payment state."""

    total: int
    por_estado: dict[str, int]
    creadas_ultimos_7_dias: int


class AdminPagosResumenResult(BaseModel):
    """Commercial state of the purchases and their payment orders."""

    compras_total: int
    compras_pagadas: int
    compras_pendientes: int
    compras_canceladas: int
    monto_pagado: float
    monto_pendiente: float
    ordenes_vencidas: int
    compras_pagadas_sin_liquidar: int


class AdminCuposResumenResult(BaseModel):
    """Capacity: contracted, paid, assigned and still free."""

    contratado: int
    pagado: int
    asignado_activo: int
    disponible_pagado: int
    inscripciones_con_capacidad_exhaustada: int


class AdminPasesResumenResult(BaseModel):
    """
    The party passes of the event — a SEPARATE block.

    The pass revenue never contaminates the sports purchase or cupo metrics:
    they are different products and they are reported apart.
    """

    pases_vendidos: int
    pases_pagados: int
    monto_pases_pagado: float
    beneficiarios_activos: int


class AdminDisciplinaConteoResult(BaseModel):
    """Teams of one discipline."""

    disciplina_id: str
    sigla: str
    nombre: str
    total: int


class AdminEquiposResumenResult(BaseModel):
    """Teams and their roster completeness."""

    total: int
    completos: int
    incompletos: int
    por_disciplina: list[AdminDisciplinaConteoResult]


class AdminParticipantesResumenResult(BaseModel):
    """People vs participations — two different numbers, never merged."""

    personas_distintas: int
    participaciones_activas: int
    en_pool: int
    sin_cupo_activo: int


class AdminAcreditacionesResumenResult(BaseModel):
    """Accreditations and the effective fiesta access."""

    total: int
    por_estado: dict[str, int]
    con_acceso_fiesta: int
    bloqueadas_por_admin: int


class AdminAccesosResumenResult(BaseModel):
    """Access log counters."""

    permitidos: int
    denegados: int
    ultimo_acceso: datetime | None = None


class AdminResumenResult(BaseModel):
    """The blocks of the operational overview."""

    evento: EventoResumenResult
    inscripciones: AdminInscripcionesResumenResult
    pagos: AdminPagosResumenResult
    cupos: AdminCuposResumenResult
    pases: AdminPasesResumenResult
    equipos: AdminEquiposResumenResult
    participantes: AdminParticipantesResumenResult
    acreditaciones: AdminAcreditacionesResumenResult
    accesos: AdminAccesosResumenResult


__all__ = [
    "EventoResumenResult",
    "AdminInscripcionesResumenResult",
    "AdminPagosResumenResult",
    "AdminCuposResumenResult",
    "AdminPasesResumenResult",
    "AdminDisciplinaConteoResult",
    "AdminEquiposResumenResult",
    "AdminParticipantesResumenResult",
    "AdminAcreditacionesResumenResult",
    "AdminAccesosResumenResult",
    "AdminResumenResult",
]
