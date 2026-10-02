"""HTTP schemas for Inscripcion."""

import re
from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import Field, model_validator, field_validator

from modules.inscripciones.presentation.schemas.equipo_schemas import (
    EquipoDetalleOut,
    ParticipanteOut as _ParticipanteOutBase,
)


# Re-export the canonical ParticipanteOut so endpoints stay shape-compatible
# with `InscripcionDetalleOut.equipos[].participantes[]`. Both detail and
# edit/move responses must produce the same fields (incl. `persona`,
# `acepto_bases`, `acepto_aptitud_fisica`, `acepto_imagen`, `notas`) so
# the frontend cache can do optimistic updates without breaking the array's
# homogeneity.
ParticipanteOut = _ParticipanteOutBase


# ── Input Schemas ────────────────────────────────────────────────────────────


class ParticipanteCreateIn(Schema):
    """
    Participant data within team creation.

    Supports two modes:
    - Legacy: provide an existing `persona_id` (UUID of an existing Persona).
    - Inline: provide persona data inline (tipoDocumento, numeroDocumento,
      nombres, apellidos, genero). The system will lookup by document and
      reuse an existing Persona or create a new one.

    At least one mode must be complete. Mixing is not allowed.
    """

    # ── Legacy mode ────────────────────────────────────────────────────────
    persona_id: str | None = None

    # ── Inline mode ────────────────────────────────────────────────────────
    tipoDocumento: Literal["DNI", "CE", "PAS"] | None = None
    numeroDocumento: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    genero: Literal["M", "F"] | None = None
    telefono: str | None = None
    whatsapp: str | None = None

    # ── Shared ────────────────────────────────────────────────────────────
    rol: str = "JUGADOR"
    talle_camiseta: str | None = None
    aseguradora_nombre: str | None = None
    aseguradora_numero_poliza: str | None = None
    notas: str | None = None
    acepto_bases: bool = False
    acepto_aptitud_fisica: bool = False
    acepto_imagen: bool = False

    @model_validator(mode="after")
    def require_one_mode(self):
        """Exactly one of legacy (persona_id) or inline (tipoDocumento) must be provided."""
        has_legacy = bool(self.persona_id)
        has_inline = bool(self.tipoDocumento and self.numeroDocumento)

        if not has_legacy and not has_inline:
            raise ValueError(
                "Debe proporcionar 'persona_id' o datos inline de persona "
                "(tipoDocumento, numeroDocumento)."
            )
        if has_legacy and has_inline:
            raise ValueError(
                "No puede proporcionar 'persona_id' y datos inline de persona al mismo tiempo. "
                "Use uno u otro."
            )
        return self

    @model_validator(mode="after")
    def require_inline_fields(self):
        """If using inline mode, all required identity fields must be present."""
        if self.persona_id:
            return self  # Legacy mode — no further validation needed

        missing = []
        if not self.tipoDocumento:
            missing.append("tipoDocumento")
        if not self.numeroDocumento:
            missing.append("numeroDocumento")
        if not self.nombres:
            missing.append("nombres")
        if not self.apellidos:
            missing.append("apellidos")
        if not self.genero:
            missing.append("genero")

        if missing:
            raise ValueError(
                f"En modo inline faltan campos requeridos: {', '.join(missing)}"
            )
        return self

    @field_validator("numeroDocumento", mode="after")
    @classmethod
    def validar_numero_documento(cls, v, info):
        """Validate document number format per document type."""
        if not v:
            return v
        tipo = info.data.get("tipoDocumento") if isinstance(info.data, dict) else getattr(info, "data", {}).get("tipoDocumento")
        if not tipo:
            return v
        v = v.strip()
        if tipo == "DNI":
            if not re.fullmatch(r"\d{8}", v):
                raise ValueError("DNI debe contener exactamente 8 dígitos")
        elif tipo == "CE":
            if not re.fullmatch(r"\d{9}", v):
                raise ValueError("CE debe contener exactamente 9 dígitos")
        elif tipo == "PAS":
            if not re.fullmatch(r"[A-Za-z0-9]{4,}", v):
                raise ValueError("PAS debe contener mínimo 4 caracteres alfanuméricos")
            v = v.upper()
        return v

    @field_validator("telefono", mode="after")
    @classmethod
    def validar_telefono(cls, v):
        """Validate phone format: 9 digits if provided."""
        if v is None:
            return v
        v = v.strip()
        if v and not re.fullmatch(r"\d{9}", v):
            raise ValueError("Teléfono debe tener exactamente 9 dígitos")
        return v

    @field_validator("whatsapp", mode="after")
    @classmethod
    def validar_whatsapp(cls, v):
        """Validate WhatsApp format: 9 digits if provided."""
        if v is None:
            return v
        v = v.strip()
        if v and not re.fullmatch(r"\d{9}", v):
            raise ValueError("WhatsApp debe tener exactamente 9 dígitos")
        return v


class EquipoCreateIn(Schema):
    """Team data within inscription creation.

    `categoria_id` is optional and not yet resolved by the wizard — frontend
    sends `null` until categorias are wired in.
    """

    disciplina_id: str
    categoria_id: str | None = None
    nombre: str
    participantes: list[ParticipanteCreateIn] = Field(default_factory=list)


class InscripcionCreateIn(Schema):
    """Request schema for creating an inscription (wizard step 1-4).

    `evento_id` is NOT an input field. The active event is resolved internally
    by `CrearInscripcionFlujo` from `EVENTO_ACTIVO_NOMBRE` in settings.
    """

    paquete_id: str
    promocion_id: str
    fusion_promocion_id: str | None = None
    observacion: str | None = None
    equipos: list[EquipoCreateIn] = Field(default_factory=list)
    # Acceptances (frontend-friendly aliases supported via field alias)
    accepted_bases: bool | None = Field(default=None, alias="acceptedBases")
    fitness_declaration: bool | None = Field(default=None, alias="fitnessDeclaration")
    image_consent: bool | None = Field(default=None, alias="imageConsent")

    model_config = {"populate_by_name": True}


class CambiarEstadoIn(Schema):
    """Request schema for changing inscription state."""

    nuevo_estado: str
    observacion: str | None = None


class AsignarDelegadoIn(Schema):
    """Request schema for assigning a delegate."""

    persona_id: str


class ParticipanteEditIn(Schema):
    """Request schema for editing a participant's rol, talle_camiseta, insurance, and notes."""

    rol: str | None = None
    talle_camiseta: str | None = None
    aseguradora_nombre: str | None = None
    aseguradora_numero_poliza: str | None = None
    notas: str | None = None


class ParticipanteMoveIn(Schema):
    """Request schema for moving a participant to another equipo."""

    equipo_destino_id: str


class ParticipantesPatchIn(Schema):
    """
    Request schema for adding participants to an existing equipo.

    Supports adding one or more participants in a single request.
    Each participant follows the same semantics as ParticipanteCreateIn:
    - Legacy mode: provide an existing persona_id
    - Inline mode: provide persona data (tipoDocumento, numeroDocumento, etc.)
    """

    participantes: list[ParticipanteCreateIn]


class AgregarParticipantesOut(Schema):
    """
    Response payload for batch-add participantes to an existing equipo.

    Returns the created `ParticipanteOut[]` entities so the frontend can do an
    optimistic append into its TanStack Query cache (`inscripcion-detalle`)
    without a full refetch. The shape of each `participante` is the SAME
    canonical `ParticipanteOut` used by the detail presenter (incl. `persona`,
    `acepto_*`, `notas`) so the array stays homogeneous —
    `equipos[].participantes[]` looks identical whether items come from the
    detail refetch or from this response.

    The human-readable success text lives at the top-level `message` of the
    envelope (consumed by `useApiUpdate` auto-toast or by the view directly).
    """

    participantes: list[ParticipanteOut]


class AgregarParticipanteOut(Schema):
    """
    Response envelope for single-add participante (used by the "Yo" / quick-add
    flow). Returns the created entity so the frontend can append it to the
    cache without a refetch. Same shape rationale as `AgregarParticipantesOut`.
    """

    mensaje: str
    participante: ParticipanteOut


# ── Output Schemas ───────────────────────────────────────────────────────────


class EventoResumenOut(Schema):
    """Minimal event info for inscription responses."""

    id: str
    nombre: str


class PaqueteResumenOut(Schema):
    """Minimal package info for inscription responses."""

    id: str
    nombre: str


class PromocionResumenOut(Schema):
    """Minimal promocion info for inscription responses."""

    id: str
    anio: int
    nombre: str


class InscripcionOut(Schema):
    """Basic inscription response."""

    id: str
    evento_id: str
    responsable_id: str
    paquete_id: str
    promocion: PromocionResumenOut
    fusion_promocion: PromocionResumenOut | None = None
    estado: str
    observacion: str | None = None
    created_at: datetime
    paquete_nombre: str | None = None
    evento_nombre: str | None = None
    promocion_nombre: str | None = None
    fusion_promocion_nombre: str | None = None
    cantidad_equipos: int = 0
    cantidad_participantes: int = 0


class DelegadoOut(Schema):
    """Delegado response."""

    id: str
    inscripcion_id: str
    persona_id: str
    persona_nombre: str | None = None
    persona_numero_documento: str | None = None


# `ParticipanteOut` is re-exported above from `equipo_schemas` so all
# endpoints (detail / edit / move) produce the SAME shape. The frontend
# cache relies on this homogeneity for in-place (optimistic) updates.


# ── InscripcionDetalleOut ────────────────────────────────────────────────────


class InscripcionDetalleOut(Schema):
    """Detailed inscription response with related data."""

    id: str
    evento_id: str
    responsable_id: str
    paquete_id: str
    promocion: PromocionResumenOut
    fusion_promocion: PromocionResumenOut | None = None
    estado: str
    observacion: str | None = None
    created_at: datetime
    evento: "EventoResumenOut"
    paquete: "PaqueteResumenOut"
    equipos: list[EquipoDetalleOut] = Field(default_factory=list)
    delegado: "DelegadoOut | None" = None
    responsable_acepto_bases: bool = False
    responsable_acepto_aptitud_fisica: bool = False
    responsable_acepto_imagen: bool = False
