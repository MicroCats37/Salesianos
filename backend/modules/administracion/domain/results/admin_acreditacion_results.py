"""
Result DTOs of the accreditations and the access log (A10, A11, A12).

`AcreditacionEvento.codigo_qr` is a LIVE BEARER CREDENTIAL — the token the QR
scanner submits to `POST /api/acceso/registrar`. It is ABSENT from every
result of this module: the administrative surface reports the operational
state of the credential, never the credential itself.
"""

from datetime import datetime

from pydantic import BaseModel


class AdminAcreditacionListItemResult(BaseModel):
    """An accreditation with its access counters."""

    id: str
    persona_id: str
    persona_nombre: str
    persona_documento: str
    estado: str
    acceso_fiesta: bool
    acceso_box: bool | None = None
    autorizacion_fiesta: str
    habilitado: bool | None = None
    observacion: str = ""
    accesos_permitidos: int
    ultimo_acceso: datetime | None = None


class AdminAccesoListItemResult(BaseModel):
    """An access attempt recorded by a scanner."""

    id: str
    acreditacion_id: str
    persona_nombre: str
    persona_documento: str
    resultado: str
    punto_acceso: str | None = None
    operador_nombre: str | None = None
    fecha_hora: datetime


class AdminAcreditacionDetalleResult(AdminAcreditacionListItemResult):
    """The drilldown of an accreditation (A11)."""

    accesos: list[AdminAccesoListItemResult] = []


__all__ = [
    "AdminAcreditacionListItemResult",
    "AdminAccesoListItemResult",
    "AdminAcreditacionDetalleResult",
]
