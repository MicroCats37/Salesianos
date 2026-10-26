"""
HTTP wrappers of the accreditations and of the access log (A10, A11, A12).

`codigo_qr` is ABSENT from every wrapper: it is a live bearer credential and
must never travel in a read payload. It is delivered only by the explicit,
admin-only QR generation action of the owning module.
"""
from datetime import datetime
from typing import Optional

from core.types import BaseSchema


class AdminAccesoListItemOut(BaseSchema):
    """An access attempt recorded by a scanner."""

    id: str
    acreditacion_id: str
    persona_nombre: str
    persona_documento: str
    resultado: str
    punto_acceso: Optional[str] = None
    operador_nombre: Optional[str] = None
    fecha_hora: datetime


class AdminAcreditacionListItemOut(BaseSchema):
    """An accreditation with its access counters."""

    id: str
    persona_id: str
    persona_nombre: str
    persona_documento: str
    estado: str
    acceso_fiesta: bool
    acceso_box: Optional[bool] = None
    autorizacion_fiesta: str
    habilitado: Optional[bool] = None
    observacion: str = ""
    accesos_permitidos: int
    ultimo_acceso: Optional[datetime] = None


class AdminAcreditacionDetailOut(AdminAcreditacionListItemOut):
    """The drilldown of an accreditation (A11)."""

    accesos: list[AdminAccesoListItemOut] = []


__all__ = [
    "AdminAccesoListItemOut",
    "AdminAcreditacionListItemOut",
    "AdminAcreditacionDetailOut",
]
