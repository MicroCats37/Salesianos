"""
HTTP schemas for AcreditacionEvento — Ninja/Schema request and response shapes.
"""
from pydantic import BaseModel, Field


# ── Obtener acreditacion ─────────────────────────────────────────────────────
class AcreditacionOut(BaseModel):
    """Output for AcreditacionEvento detail.

    `codigo_qr` is deliberately ABSENT: the QR code is a live bearer
    credential (the token the scanner submits to `POST /api/acceso/registrar`)
    and must never travel in a general read payload. It is delivered only by
    the explicit, admin-only `POST /api/acreditaciones/{e}/{p}/generar-qr`
    action, whose schema is `GenerarQROut`.
    """

    acreditacion_id: str = Field(..., description="Acreditacion UUID")
    evento_id: str = Field(..., description="Evento UUID")
    persona_id: str = Field(..., description="Persona UUID")
    estado: str = Field(..., description="Estado")
    acceso_fiesta: bool = Field(..., description="Effective fiesta access")
    acceso_box: bool | None = Field(None, description="Box access (deferred)")
    autorizacion_fiesta: str = Field(..., description="AUTOMATICA/AUTORIZADA/BLOQUEADA")
    habilitado: bool | None = Field(None, description="Admin override")
    observacion: str = Field("", description="Administrative observation")


# ── Override fiesta ───────────────────────────────────────────────────────────

class OverrideFiestaIn(BaseModel):
    """Input for admin fiesta override."""
    autorizacion: str = Field(
        ...,
        description="AUTORIZADA or BLOQUEADA",
    )
    motivo: str = Field(..., description="Reason for override")


class OverrideFiestaOut(BaseModel):
    """Output from applying fiesta override."""
    persona_id: str = Field(..., description="Persona UUID")
    evento_id: str = Field(..., description="Evento UUID")
    autorizacion_fiesta: str = Field(..., description="New autorizacion")
    acceso_fiesta: bool = Field(..., description="Effective acceso_fiesta")
    observacion: str = Field(..., description="Audit observation")


# ── Generar QR ───────────────────────────────────────────────────────────────

class GenerarQROut(BaseModel):
    """Output from regenerating QR code."""
    acreditacion_id: str = Field(..., description="Acreditacion UUID")
    codigo_qr: str = Field(..., description="New QR code UUID")


# ── Registrar acceso (QR scan) ────────────────────────────────────────────────

class RegistrarAccesoIn(BaseModel):
    """Input for QR scan access registration."""
    qr_token: str = Field(..., description="UUID token from QR code")
    punto_acceso: str | None = Field(None, description="Scanner location")


class RegistrarAccesoOut(BaseModel):
    """Output from registering access attempt."""
    resultado: str = Field(..., description="PERMITIDO or DENEGADO")
    persona: str | None = Field(None, description="Person name if known")
    acceso_fiesta: bool = Field(..., description="Whether fiesta access is granted")
    timestamp: str = Field(..., description="Access attempt timestamp")
