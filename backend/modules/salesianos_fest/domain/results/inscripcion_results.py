"""Result DTOs for inscripcion queries."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


# ─── Nested result DTOs for related commerce/payment ───────────────────────────


@dataclass
class OrdenPagoResult:
    """Result for OrdenPago — payment order summary (no metadata exposed)."""

    id: str
    numero: str
    estado: str
    pagada_en: Optional[datetime] = None


@dataclass
class CompraResult:
    """Result for a FEST commercial purchase (CompraInscripcion + Compra + OrdenPago).

    The selector loads this for display in the detail presenter.
    NO derived state (estado_roster, resumen_pago) is calculated here — only raw data.
    """

    id: str
    tipo: str  # INICIAL or AMPLIACION
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    estado: str  # PENDIENTE, PAGADA, CANCELADA
    orden_pago: Optional[OrdenPagoResult] = None


@dataclass
class InscripcionResult:
    """Result for inscripcion query."""

    id: str
    evento_id: str
    evento_nombre: str
    responsable_id: str
    responsable_nombre: str
    paquete_id: str
    paquete_nombre: str
    promocion_id: str
    promocion_nombre: str
    fusion_promocion_id: Optional[str]
    delegado_id: Optional[str]
    estado: str
    observacion: str
    created_at: datetime


@dataclass
class InscripcionDetailResult:
    """Result for inscripcion detail with equipos, personas and commerce data.

    NO derived state (estado_roster, resumen_equipos, resumen_pago) is
    calculated here — only raw loaded data. The presenter computes derived
    fields from this result.
    """

    id: str
    evento_id: str
    evento_nombre: str
    responsable_id: str
    responsable_nombre: str
    paquete_id: str
    paquete_nombre: str
    promocion_id: str
    promocion_nombre: str
    fusion_promocion_id: Optional[str]
    delegado_id: Optional[str]
    delegado_nombre: Optional[str]
    estado: str
    observacion: str
    created_at: datetime
    equipos: list["EquipoResult"]
    personas: list["InscripcionPersonaResult"]
    compras: list[CompraResult] = None  # FEST purchases via CompraInscripcion
    # Raw count of ACTIVA AsignacionCupo funded by this inscripcion's PAGADA
    # compras. Loaded by the selector so the presenter can derive the free
    # paid capacity WITHOUT any ORM access (presenters stay pure transformers).
    asignados_pagados: int = 0

    def __post_init__(self):
        if self.compras is None:
            self.compras = []


@dataclass
class EquipoResult:
    """Result for equipo query.

    Includes min_jugadores (Disciplina.min_jugadores) for presenter
    to calculate estado_roster without additional DB queries.
    When loaded via InscripcionSelector.get_by_id_with_details, min_jugadores
    is always populated. Other selector paths may leave it as None.
    """

    id: str
    inscripcion_id: str
    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    min_jugadores: Optional[int] = None  # Disciplina.min_jugadores — loaded by selector
    categoria_id: Optional[str] = None
    categoria_nombre: Optional[str] = None
    nombre: str = ""
    estado: str = ""
    created_at: Optional[datetime] = None
    participaciones: list["ParticipacionResult"] = None

    def __post_init__(self):
        if self.participaciones is None:
            self.participaciones = []


@dataclass
class InscripcionPersonaResult:
    """Result for inscripcion persona query."""

    id: str
    inscripcion_id: str
    persona_id: str
    persona_nombre: str  # "Juan Pérez" (combined, backward-compat)
    persona_numero_documento: str
    estado: str
    created_at: datetime
    persona_nombres: Optional[str] = None  # "Juan" (separated, opcional)
    persona_apellidos: Optional[str] = None  # "Pérez" (separated, opcional)


@dataclass
class ParticipacionResult:
    """Result for participacion query."""

    id: str
    inscripcion_persona_id: str
    equipo_id: str
    equipo_nombre: str
    evento_id: str
    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    persona_id: str
    persona_nombre: str  # "Juan Pérez" (combined, backward-compat)
    persona_numero_documento: str
    rol: str
    talla_camiseta: str
    notas: str
    estado: str
    created_at: datetime
    persona_nombres: Optional[str] = None  # "Juan" (separated, opcional)
    persona_apellidos: Optional[str] = None  # "Pérez" (separated, opcional)


@dataclass
class InscripcionCompletaResult:
    """Result for atomic inscription + compra + equipos creation."""

    inscripcion_id: str
    inscripcion_estado: str
    compra_id: str
    compra_inscripcion_id: str
    orden_pago_id: str
    compra_estado: str
    cantidad: int
    precio_unitario: float
    total: float
    equipos: list["EquipoResult"]


@dataclass
class PoolEntryResult:
    """Result for a participant in the pre-registration pool (no equipo assigned).

    Exposes only UI-safe, authorized details. No payment metadata (compra data)
    is included — the pool entry only tells whether the person is eligible to
    join a team.

    Eligibility is determined by the presence of an ACTIVA AsignacionCupo
    linked to this inscripcion_persona. No equipo means no Participacion exists.
    """

    id: str  # InscripcionPersona.id
    persona_id: str
    persona_nombre: str  # "Juan Pérez"
    persona_nombres: str
    persona_apellidos: str
    persona_numero_documento: str
    estado: str  # InscripcionPersona estado (A/R)
    created_at: datetime
    # Eligibility to join a team
    tiene_cupo_activo: bool
    # Typed eligibility discriminator for the UI (see EstadoPoolChoices).
    # LISTO | ESPERANDO_PAGO | SIN_CAPACIDAD | CUPO_POR_ASIGNAR.
    estado_pool: str
    # Null when tiene_cupo_activo is True; a UI-safe reason string when False.
    # Never exposes internal IDs, constraint names, or payment metadata.
    motivo_bloqueo: Optional[str]


@dataclass
class DisciplinaAsignadaResult:
    """A discipline where the person already holds an ACTIVE participation.

    One paid cup authorises the person in EVERY contracted discipline, so the
    same `inscripcion_persona` can appear here more than once — once per
    discipline. It can never appear twice for the SAME discipline (R11).
    """

    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    equipo_id: str
    equipo_nombre: str


@dataclass
class ElegibleResult:
    """Result for one candidate of the team-scoped participant selector.

    The backend owns the whole verdict: the UI never re-derives whether a
    person may join the target team. It renders what this DTO says.
    """

    id: str  # InscripcionPersona.id
    persona_id: str
    persona_nombre: str
    persona_nombres: str
    persona_apellidos: str
    persona_numero_documento: str
    estado: str  # InscripcionPersona estado (A/R)
    created_at: datetime
    # Commercial eligibility — the same typed discriminator the pool uses.
    tiene_cupo_activo: bool
    estado_pool: str  # LISTO | ESPERANDO_PAGO | SIN_CAPACIDAD | CUPO_POR_ASIGNAR
    # UI-safe reason why there is no paid cup. None when the cup is active.
    motivo_bloqueo: Optional[str]
    # Disciplines where the person already plays — drives the "también juega
    # en ..." chips and the R11 verdict for the target discipline.
    disciplinas_asignadas: list[DisciplinaAsignadaResult]
    # Typed R11 flag: the person already plays in the TARGET discipline.
    # It is a boolean, never a reason string — the UI never parses prose.
    ya_en_disciplina: bool
    # Backend verdict for the TARGET team: the person may be added now.
    asignable: bool
    # UI-safe reason when asignable is False. None when asignable is True.
    motivo_no_asignable: Optional[str]


@dataclass
class ElegiblesEquipoResult:
    """Team-scoped candidate list with the target team context."""

    inscripcion_id: str
    equipo_id: str
    equipo_nombre: str
    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    elegibles: list[ElegibleResult]
