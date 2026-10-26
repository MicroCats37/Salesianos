"""Internal DTO schemas for inscripcion domain — NOT HTTP schemas."""
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel as PydanticBaseModel, model_validator


class PersonaInlineData(PydanticBaseModel):
    """Inline persona data for creating a new persona atomically with an inscripcion.

    Used when the caller does NOT yet have a `persona_id` (e.g., the dashboard
    lets the user add a brand new player without going through user registration
    first). Mirrors the model `modules.usuarios.domain.models.Persona` —
    see PersonaInlineIn in the presentation layer for the HTTP counterpart.
    """

    tipo_documento: Literal["DNI", "CE", "PAS"]
    numero_documento: str
    nombres: str
    apellidos: str
    genero: Literal["M", "F"]
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None


class InscripcionCreateData(PydanticBaseModel):
    """Data for creating an inscripcion.

    responsable_id is optional — when omitted the controller injects it
    from the authenticated user's Persona (server-derived ownership).
    """

    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    estado: str = "BORRADOR"
    observacion: str = ""
    responsable_id: Optional[str] = None  # Injected by controller from request.auth


class EquipoCreateData(PydanticBaseModel):
    """Data for creating an equipo."""

    inscripcion_id: str
    disciplina_id: str
    categoria_id: Optional[str] = None
    promocion_id: Optional[str] = None
    nombre: str
    estado: str = "EQUIPO_ACTIVO"


class InscripcionPersonaCreateData(PydanticBaseModel):
    """Data for adding a person to an inscripcion.

    The caller must supply EITHER `persona_id` (existing persona) OR
    `persona_data` (inline creation of a new persona). Exactly one of the
    two is required. The flow upserts by (tipo_documento, numero_documento),
    so a repeated request with the same `persona_data` is idempotent.

    Pool-first rule: `persona_data` (a NEW person) can NEVER be combined with
    `equipo_id`. A brand-new participant is created in the pool only
    (`equipo_id = None`); placing somebody in a team is a second, separate
    operation (`POST /inscripciones/{id}/pool/asignar`). The combination is
    rejected by the input guard `_no_equipo_con_persona_data` with the stable
    code `PARTICIPANTE_DEBE_PREREGISTRARSE` (422).
    """

    inscripcion_id: str
    persona_id: Optional[str] = None
    persona_data: Optional["PersonaInlineData"] = None
    equipo_id: Optional[str] = None  # If provided, creates Participacion atomically
    estado: str = "A"
    aceptaciones: Optional[list[Literal["BASES", "APTITUD_FISICA", "IMAGEN"]]] = None
    actor_id: Optional[str] = None
    medio: str = "WEB"
    ip_address: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_persona_source(self) -> "InscripcionPersonaCreateData":
        present = [v for v in (self.persona_id, self.persona_data) if v is not None]
        if len(present) != 1:
            from modules.salesianos_fest.domain.exceptions import (
                PersonaDataRequiredError,
            )
            raise PersonaDataRequiredError()
        return self

    @model_validator(mode="after")
    def _no_equipo_con_persona_data(self) -> "InscripcionPersonaCreateData":
        """Input guard: a new person cannot be created inside a team.

        The pool is the ONLY entry point of the participant lifecycle: the
        preregistration creates the `Persona` and the `InscripcionPersona` and
        claims the paid cup when there is free capacity. Creating the person
        and the `Participacion` in one shot (`persona_data` + `equipo_id`)
        would bypass the pool and the FIFO cup allocator.
        """
        if self.persona_data is not None and self.equipo_id is not None:
            from modules.salesianos_fest.domain.exceptions import (
                ParticipanteDebePreregistrarseError,
            )
            raise ParticipanteDebePreregistrarseError()
        return self


class ParticipacionCreateData(PydanticBaseModel):
    """Data for creating a participacion."""

    inscripcion_persona_id: str
    equipo_id: str
    rol: str = "J"
    talla_camiseta: str = ""
    notas: str = ""
    estado: str = "A"


class ParticipacionUpdateData(PydanticBaseModel):
    """Data for updating a participacion."""

    rol: Optional[str] = None
    talla_camiseta: Optional[str] = None
    notas: Optional[str] = None
    estado: Optional[str] = None


class InscripcionUpdateData(PydanticBaseModel):
    """Data for updating an inscripcion."""

    estado: Optional[str] = None
    observacion: Optional[str] = None
    delegado_id: Optional[str] = None


class EquipoUpdateData(PydanticBaseModel):
    """Data for updating an equipo."""

    nombre: Optional[str] = None
    estado: Optional[str] = None


class EquipoCreateSinInscripcionData(PydanticBaseModel):
    """Data for an equipo to be created inside an atomic inscription flow.

    Does NOT include inscripcion_id — the atomic flow injects it.
    """

    disciplina_id: str
    categoria_id: Optional[str] = None
    nombre: str
    estado: str = "EQUIPO_ACTIVO"


class InscripcionCompletaCreateData(PydanticBaseModel):
    """Data for atomic inscription + compra + equipos creation.

    responsible_id is derived server-side from authenticated user.
    equipos are created atomically with the inscription.
    cantidad is validated against paquete.minimo_compra_inicial.
    precio_unitario_cotizado is optional — if sent, server revalidates it against
    the current catalog price and raises PrecioCambioError if they differ.
    cotizacion_version is metadata only — server does NOT validate it yet, but
    stores/logs it for traceability of which quotation snapshot was used.
    """

    evento_id: str
    paquete_id: str
    promocion_id: str
    fusion_promocion_id: Optional[str] = None
    delegado_id: Optional[str] = None
    cantidad: int  # Required initial purchase quantity (>= minimo_compra_inicial)
    equipos: list[EquipoCreateSinInscripcionData]
    aceptaciones: Optional[list[str]] = None  # ["BASES", "APTITUD_FISICA", "IMAGEN"]
    estado: str = "BORRADOR"
    observacion: str = ""
    precio_unitario_cotizado: Optional[float] = None  # If sent, triggers price revalidation
    cotizacion_version: Optional[int] = None  # Metadata — not validated yet
    # responsable_id injected by controller from request.auth — NOT from client
