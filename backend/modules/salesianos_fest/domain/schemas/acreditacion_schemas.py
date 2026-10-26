"""
Internal DTOs for AcreditacionEvento domain operations.
"""
from pydantic import BaseModel


class OverrideFiestaData(BaseModel):
    """Data for admin fiesta override."""
    autorizacion: str  # AUTORIZADA or BLOQUEADA
    motivo: str


class AcreditacionResult(BaseModel):
    """Result of an AcreditacionEvento operation."""
    acreditacion_id: str
    evento_id: str
    persona_id: str
    estado: str
    acceso_fiesta: bool
    autorizacion_fiesta: str
    habilitado: bool | None


class AccesoRegistradoResult(BaseModel):
    """Result of registering an access attempt."""
    resultado: str  # PERMITIDO or DENEGADO
    persona_nombre: str | None = None
    acceso_fiesta: bool
    timestamp: str | None = None
