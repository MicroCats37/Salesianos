"""
Result DTOs for AcreditacionEvento operations — returned by services to orchestrators.
"""
from dataclasses import dataclass


@dataclass
class AcreditacionResult:
    """Result of an AcreditacionEvento operation."""
    acreditacion_id: str
    evento_id: str
    persona_id: str
    estado: str
    acceso_fiesta: bool
    autorizacion_fiesta: str
    habilitado: bool | None = None


@dataclass
class OverrideFiestaResult:
    """Result of an admin fiesta override."""
    persona_id: str
    evento_id: str
    autorizacion_fiesta: str
    acceso_fiesta: bool
    observacion: str
@dataclass
class AccesoRegistradoResult:
    """Result of registering an access attempt."""

    resultado: str
    persona_nombre: str | None = None
    acceso_fiesta: bool = False
    timestamp: str | None = None


@dataclass
class GenerarQRResult:
    """Result of the admin-only QR regeneration action.

    `codigo_qr` is the LIVE bearer credential. It travels only through this
    result — and therefore only through the explicit, admin-only
    `POST /api/acreditaciones/{e}/{p}/generar-qr` endpoint. No general read
    payload ever carries it.
    """

    acreditacion_id: str
    codigo_qr: str

