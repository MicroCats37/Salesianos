"""
AdminResumenOut — HTTP wrapper of the operational overview (A1).

ONE explicitly named wrapper per block — never a generic `data`/`contexto`
envelope (`contract/api-wrapper-presenter-contract.md` §5). Every number is
computed by the backend; the frontend never re-derives counts, balances or
eligibility (`contract/api-wrapper-presenter-contract.md` §7).

The block schemas are COMPOSED (not inherited) into `AdminResumenOut`, which
is the intent of `contract/SCHEMA_DRY_INTENTION.md`: the identity block, the
specific blocks and the aggregate are reusable pieces.
"""
from datetime import date, datetime
from typing import Optional

from core.types import BaseSchema


class EventoResumenOut(BaseSchema):
    """Identity and calendar of the active event."""

    id: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    esta_activo: bool
    fecha_limite_modificacion: Optional[date] = None
    puede_modificar: bool


class AdminInscripcionesResumenOut(BaseSchema):
    """Administrative counters of the registrations.

    The state of a registration NEVER reflects the payment: the commercial
    state lives in the `pagos` block.
    """

    total: int
    por_estado: dict[str, int]
    creadas_ultimos_7_dias: int


class AdminPagosResumenOut(BaseSchema):
    """Commercial counters of the purchases and their payment orders."""

    compras_total: int
    compras_pagadas: int
    compras_pendientes: int
    compras_canceladas: int
    monto_pagado: float
    monto_pendiente: float
    ordenes_vencidas: int
    compras_pagadas_sin_liquidar: int


class AdminCuposResumenOut(BaseSchema):
    """Capacity: contracted, paid, assigned and still free."""

    contratado: int
    pagado: int
    asignado_activo: int
    disponible_pagado: int
    inscripciones_con_capacidad_exhaustada: int


class AdminPasesResumenOut(BaseSchema):
    """
    The party passes of the event — a SEPARATE block.

    The pass revenue never contaminates the sports purchase or cupo metrics:
    they are different products and they are reported apart.
    """

    pases_vendidos: int
    pases_pagados: int
    monto_pases_pagado: float
    beneficiarios_activos: int


class AdminDisciplinaConteoOut(BaseSchema):
    """Teams of one discipline."""

    disciplina_id: str
    sigla: str
    nombre: str
    total: int


class AdminEquiposResumenOut(BaseSchema):
    """Teams and their roster completeness."""

    total: int
    completos: int
    incompletos: int
    por_disciplina: list[AdminDisciplinaConteoOut]


class AdminParticipantesResumenOut(BaseSchema):
    """People vs participations — two different numbers, never merged."""

    personas_distintas: int
    participaciones_activas: int
    en_pool: int
    sin_cupo_activo: int


class AdminAcreditacionesResumenOut(BaseSchema):
    """Accreditations and the effective fiesta access."""

    total: int
    por_estado: dict[str, int]
    con_acceso_fiesta: int
    bloqueadas_por_admin: int


class AdminAccesosResumenOut(BaseSchema):
    """Access log counters."""

    permitidos: int
    denegados: int
    ultimo_acceso: Optional[datetime] = None


class AdminResumenOut(BaseSchema):
    """The blocks of the operational overview."""

    evento: EventoResumenOut
    inscripciones: AdminInscripcionesResumenOut
    pagos: AdminPagosResumenOut
    cupos: AdminCuposResumenOut
    pases: AdminPasesResumenOut
    equipos: AdminEquiposResumenOut
    participantes: AdminParticipantesResumenOut
    acreditaciones: AdminAcreditacionesResumenOut
    accesos: AdminAccesosResumenOut


__all__ = [
    "EventoResumenOut",
    "AdminInscripcionesResumenOut",
    "AdminPagosResumenOut",
    "AdminCuposResumenOut",
    "AdminPasesResumenOut",
    "AdminDisciplinaConteoOut",
    "AdminEquiposResumenOut",
    "AdminParticipantesResumenOut",
    "AdminAcreditacionesResumenOut",
    "AdminAccesosResumenOut",
    "AdminResumenOut",
]
