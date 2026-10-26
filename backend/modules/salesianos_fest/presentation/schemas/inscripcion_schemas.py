"""
HTTP request/response schemas for inscripcion endpoints.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, Literal

from pydantic import Field

from core.types import BaseSchema


# ─── Shared / Blocks ──────────────────────────────────────────────────────────

class PersonaSummarySchema(BaseSchema):
    """Minimal persona info for nested responses."""

    id: str
    nombre: str  # backward-compat: nombre completo "Juan Pérez"
    nombres: Optional[str] = None  # separado para UI que necesita desdoblar
    apellidos: Optional[str] = None  # separado para UI que necesita desdoblar
    numero_documento: str


class DisciplinaSummarySchema(BaseSchema):
    """Minimal disciplina info."""

    id: str
    nombre: str
    sigla: str


class CategoriaSummarySchema(BaseSchema):
    """Minimal categoria info."""

    id: str
    nombre: str


class EquipoSummarySchema(BaseSchema):
    """Equipo info for inscripcion detail."""

    id: str
    nombre: str
    disciplina: DisciplinaSummarySchema
    categoria: Optional[CategoriaSummarySchema]
    estado: str


class EquipoDetailSchema(BaseSchema):
    """Equipo info with participantes for inscripcion detail.

    Extended in Phase 2 with roster-derived fields (estado_roster,
    jugadores_registrados, minimo_deportivo, faltantes) and persisted
    estado_equipo. The raw ``estado`` field is retained temporarily for
    backward-compatible client consumption.
    """

    id: str
    nombre: str
    disciplina: DisciplinaSummarySchema
    categoria: Optional[CategoriaSummarySchema]
    estado: str  # persisted EQUIPO_ACTIVO / EQUIPO_CANCELADO — backward-compat
    # Phase 2: persisted team state (alias of ``estado``, explicit name)
    estado_equipo: str
    # Phase 2: derived/read-only roster state — computed by presenter
    estado_roster: Literal["INCOMPLETO", "COMPLETO"]
    jugadores_registrados: int  # count of ACTIVA participaciones
    minimo_deportivo: int  # Disciplina.min_jugadores
    faltantes: int  # max(0, minimo_deportivo - jugadores_registrados)
    participantes: list["ParticipacionOut"]


class InscripcionPersonaSummarySchema(BaseSchema):
    """InscripcionPersona for inscripcion detail."""

    id: str
    persona: PersonaSummarySchema
    estado: str


class InscripcionPersonaOut(InscripcionPersonaSummarySchema):
    """Response for an inscription roster member."""

    inscripcion_id: str
    created_at: str


# ─── Request Schemas ───────────────────────────────────────────────────────────

class CrearInscripcionIn(BaseSchema):
    """Request payload for creating an inscripcion.

    Note: responsable_id is NOT accepted from the client.
    The server derives it from the authenticated user's Persona (request.auth).
    """

    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    estado: str = "BORRADOR"
    observacion: str = ""


class CrearEquipoIn(BaseSchema):
    """Request payload for creating an equipo."""

    inscripcion_id: str
    disciplina_id: str
    categoria_id: Optional[str] = None
    nombre: str
    estado: str = "EQUIPO_ACTIVO"


class PersonaInlineIn(BaseSchema):
    """Datos inline para crear una Persona al agregarla a una inscripción.

    Usado cuando el dashboard agrega un jugador nuevo (sin `persona_id`
    existente). El backend hace upsert por `(tipo_documento, numero_documento)`:
    si ya existe una Persona con ese documento, la reutiliza; si no, la crea.
    """

    tipo_documento: Literal["DNI", "CE", "PAS"]
    numero_documento: str = Field(..., max_length=20)
    nombres: str = Field(..., max_length=255)
    apellidos: str = Field(..., max_length=255)
    genero: Literal["M", "F"]
    telefono: Optional[str] = Field(None, max_length=9)
    whatsapp: Optional[str] = Field(None, max_length=9)


class AgregarPersonaIn(BaseSchema):
    """Request payload for adding a person to an inscripcion.

    Exactly one of `persona_id` (existing persona) or `persona_data`
    (inline new persona — server does upsert by documento) must be provided.
    The XOR validation is enforced in `AgregarPersonaFlujo` and surfaces
    as `PersonaDataRequiredError` (422 / PERSONA_REQUIRED).

    Pool-first rule: `persona_data` (a NEW person) MUST NOT be combined with
    `equipo_id`. The preregistration happens in the pool (no `equipo_id`) and
    the team placement is a second operation
    (`POST /inscripciones/{id}/pool/asignar`). Sending both is rejected with
    `ParticipanteDebePreregistrarseError` (422 /
    PARTICIPANTE_DEBE_PREREGISTRARSE).
    """

    persona_id: Optional[str] = None
    persona_data: Optional[PersonaInlineIn] = None
    # If provided, creates Participacion atomically — only for an ALREADY
    # registered participant (`persona_id`). Combining it with `persona_data`
    # is rejected with 422 PARTICIPANTE_DEBE_PREREGISTRARSE.
    equipo_id: Optional[str] = None
    aceptaciones: Optional[list[Literal["BASES", "APTITUD_FISICA", "IMAGEN"]]] = None


class CrearParticipacionIn(BaseSchema):
    """Request payload for creating a participacion."""

    inscripcion_persona_id: str
    equipo_id: str
    rol: str = "J"
    talla_camiseta: str = ""
    notas: str = ""


class ActualizarInscripcionIn(BaseSchema):
    """Request payload for updating an inscripcion."""

    estado: Optional[str] = None
    observacion: Optional[str] = None
    delegado_id: Optional[str] = None


class ActualizarParticipacionIn(BaseSchema):
    """Request payload for updating a participacion."""

    rol: Optional[str] = None
    talla_camiseta: Optional[str] = None
    notas: Optional[str] = None
    estado: Optional[str] = None


class MoverParticipacionIn(BaseSchema):
    """Request payload for moving a participacion to another equipo."""

    equipo_destino_id: str


class EquipoParaCrearIn(BaseSchema):
    """Equipo data inside CrearInscripcionCompletaIn — no inscripcion_id."""

    disciplina_id: str
    categoria_id: Optional[str] = None
    nombre: str
    estado: str = "EQUIPO_ACTIVO"


class CrearInscripcionCompletaIn(BaseSchema):
    """Request payload for atomic inscription + compra + equipos creation.

    responsable_id is derived server-side from the authenticated user's Persona.
    cantidad must be >= paquete.minimo_compra_inicial.
    precio_unitario_cotizado is optional — if sent, server revalidates it against
    the current catalog price and raises PrecioCambioError if they differ.
    cotizacion_version is metadata — propagated to domain for traceability, not
    validated server-side yet.
    """

    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    cantidad: int  # Required initial purchase quantity
    equipos: list[EquipoParaCrearIn]
    estado: str = "BORRADOR"
    observacion: str = ""
    precio_unitario_cotizado: Optional[float] = None  # triggers server-side price revalidation
    cotizacion_version: Optional[int] = None  # metadata, not validated


# ─── Response Schemas ─────────────────────────────────────────────────────────

class InscripcionOut(BaseSchema):
    """Response for inscripcion."""

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
    created_at: str


class InscripcionDetailOut(BaseSchema):
    """Response for inscripcion with equipos and personas.

    Extended in Phase 2 with additive resumen_equipos and resumen_pago
    summary blocks. The ``estado`` field (inscription sports/administrative
    state) is preserved for backward compatibility. Team ``estado`` is also
    preserved temporarily — see ``EquipoDetailSchema``.
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
    created_at: str
    equipos: list[EquipoDetailSchema]
    personas: list[InscripcionPersonaSummarySchema]
    # Phase 2: aggregate team roster summary
    resumen_equipos: "ResumenEquiposSchema"
    # Phase 2: aggregate payment/commercial summary
    resumen_pago: "ResumenPagoSchema"
    # Distinct people vs roster rows — one cup authorises several disciplines.
    resumen_participantes: "ResumenParticipantesSchema"


# ─── Phase 2: Summary Schemas ─────────────────────────────────────────────────

class OrdenPagoResumenSchema(BaseSchema):
    """Payment-order summary for inscripcion detail.

    Contract: ``OrdenPago.metadata`` is NEVER exposed here.
    """

    id: str
    numero: str
    estado: str
    pagada_en: Optional[str] = None


class CompraResumenSchema(BaseSchema):
    """Commercial purchase summary for inscripcion detail.

    Contract: ``Compra.metadata`` is never exposed here.
    """

    id: str
    tipo: str  # INICIAL | AMPLIACION
    cantidad: int
    precio_unitario: float
    total: float
    estado: str  # PENDIENTE | PAGADA | CANCELADA
    orden_pago: Optional[OrdenPagoResumenSchema] = None


class ResumenPagoSchema(BaseSchema):
    """Aggregate payment/commercial summary for an inscripcion.

    Orthogonal to resumen_equipos (sports roster state).
    Computed by the presenter from compras + ordenes.
    Never mutates or infers ``Inscripcion.estado`` from payment state.
    """

    total_compras: int
    total_contratado: int  # sum of quantities of non-cancelled purchases
    total_pagado: float  # sum of monetary totals of PAGADA purchases
    total_pagado_cantidad: int  # sum of quantities of PAGADA purchases
    compras_pendientes: int
    compras_pagadas: int
    compras_canceladas: int
    disponible_pagado: int  # free paid slots = total_pagado_cantidad - active assignments (asignados_pagados)
    estado_mensaje: str  # UI message: "Sin actividades de pago" | "Pago pendiente" | "Pago parcial" | "Pago confirmado"
    compras: list[CompraResumenSchema]


class ResumenEquiposSchema(BaseSchema):
    """Aggregate team-roster summary for an inscripcion.

    Computed by the presenter from equipo roster states.
    """

    total: int  # total number of equipos
    completos: int  # equipos with estado_roster == COMPLETO
    incompletos: int  # equipos with estado_roster == INCOMPLETO


class ResumenParticipantesSchema(BaseSchema):
    """Aggregate participant summary for an inscripcion.

    One paid cup authorises a person in EVERY contracted discipline, so the
    two numbers are different by design and must never be mixed:

    - `participaciones` — the ACTIVE roster rows (one per team the person
      plays in).
    - `personas` — the DISTINCT people (one per `inscripcion_persona_id`).

    `personas` is the number that can be compared against the paid cupos;
    `participaciones` is the number of roster slots filled.
    """

    participaciones: int
    personas: int


class EquipoOut(BaseSchema):
    """Response for equipo."""

    id: str
    inscripcion_id: str
    disciplina: DisciplinaSummarySchema
    categoria: Optional[CategoriaSummarySchema]
    nombre: str
    estado: str
    created_at: str


class ParticipacionOut(BaseSchema):
    """Response for participacion."""

    id: str
    inscripcion_persona_id: str
    equipo_id: str
    equipo_nombre: str
    evento_id: str
    disciplina: DisciplinaSummarySchema
    persona: PersonaSummarySchema
    rol: str
    talla_camiseta: str
    notas: str
    estado: str
    created_at: str


class InscripcionCompletaOut(BaseSchema):
    """Response for atomic inscription + compra + equipos creation."""

    inscripcion_id: str
    inscripcion_estado: str
    compra_id: str
    orden_pago_id: str
    compra_estado: str
    cantidad: int
    precio_unitario: float
    total: float
    equipos: list[EquipoOut]


# ─── Phase 3: Pool schemas ─────────────────────────────────────────────────────

class PoolEntryOut(BaseSchema):
    """A participant in the pre-registration pool (no equipo assigned).

    Exposes only UI-safe, authorized details. No payment metadata.
    tiene_cupo_activo=True → eligible to join a team.
    tiene_cupo_activo=False → motivo_bloqueo explains why (UI-safe message only).

    `estado_pool` is the typed eligibility discriminator the UI maps to a
    visual state: LISTO | ESPERANDO_PAGO | SIN_CAPACIDAD | CUPO_POR_ASIGNAR.
    It is derived, never persisted, and never mutates `InscripcionPersona.estado`.
    """

    id: str
    persona: PersonaSummarySchema
    estado: str
    created_at: str
    tiene_cupo_activo: bool
    # Typed eligibility discriminator — the UI never parses `motivo_bloqueo`
    # to decide what to render.
    estado_pool: str
    # Null when eligible; a UI-safe message when blocked.
    # NEVER exposes internal IDs, constraint names, compra data, or SQL errors.
    motivo_bloqueo: Optional[str] = None


class PoolOut(BaseSchema):
    """Response for GET /inscripciones/{id}/pool."""

    inscripcion_id: str
    pool: list[PoolEntryOut]


# ─── Team-scoped participant selector ─────────────────────────────────────────


class DisciplinaAsignadaOut(BaseSchema):
    """A discipline where the person already holds an active participation.

    One paid cup authorises the person in EVERY contracted discipline, so the
    same person can appear here once per discipline — never twice for the
    same discipline (R11).
    """

    disciplina: DisciplinaSummarySchema
    equipo_id: str
    equipo_nombre: str


class ElegibleOut(BaseSchema):
    """A candidate of the team-scoped participant selector.

    The backend owns the whole verdict: `asignable` tells whether the person
    may join the target team RIGHT NOW and `motivo_no_asignable` explains why
    not. The UI never re-derives eligibility.

    `estado_pool` is the same typed commercial discriminator the pool uses
    (LISTO | ESPERANDO_PAGO | SIN_CAPACIDAD | CUPO_POR_ASIGNAR).
    """

    id: str
    persona: PersonaSummarySchema
    estado: str
    created_at: str
    tiene_cupo_activo: bool
    estado_pool: str
    # UI-safe reason why there is no paid cup. None when the cup is active.
    motivo_bloqueo: Optional[str] = None
    # Disciplines where the person already plays.
    disciplinas_asignadas: list[DisciplinaAsignadaOut] = []
    # Typed R11 flag — the person already plays in the TARGET discipline.
    # A boolean, never a reason string: the UI never parses prose.
    ya_en_disciplina: bool
    # Backend verdict for the target team.
    asignable: bool
    # UI-safe reason when asignable is False. None when asignable is True.
    motivo_no_asignable: Optional[str] = None


class ElegiblesEquipoOut(BaseSchema):
    """Response for GET /inscripciones/{id}/equipos/{equipo_id}/elegibles."""

    inscripcion_id: str
    equipo_id: str
    equipo_nombre: str
    disciplina: DisciplinaSummarySchema
    elegibles: list[ElegibleOut]


class AsignarAEquipoIn(BaseSchema):
    """Request payload for assigning an existing participant to an equipo.

    This is the SOLE authoritative endpoint for assigning a participant to an
    equipo. It is called by the frontend from the participant selector modal.
    Phase 2 gates (cup, R11, roster) are enforced inside the mutation.
    """

    inscripcion_persona_id: str
    equipo_id: str
    rol: str = "J"
    talla_camiseta: str = ""
    notas: str = ""
