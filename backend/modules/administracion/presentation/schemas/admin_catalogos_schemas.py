"""
AdminCatalogosOut — HTTP wrapper of the filter catalogs (A2).

The catalogs expose OPTION LISTS only: identifiers, display names and the
state vocabularies of the owning modules. No PII, no credential, no payment
detail and no QR ever travels through this wrapper.
"""
from typing import Optional

from core.types import BaseSchema


class AdminCatalogoItemOut(BaseSchema):
    """A filter option of a catalog."""

    id: str
    nombre: str
    sigla: Optional[str] = None


class AdminCatalogoPaqueteOut(BaseSchema):
    """A package filter option."""

    id: str
    nombre: str
    tipo: str


class AdminEstadosCatalogosOut(BaseSchema):
    """The state vocabularies the filters use."""

    inscripcion: list[str]
    compra: list[str]
    orden_pago: list[str]
    asignacion_cupo: list[str]
    equipo: list[str]
    acreditacion: list[str]
    autorizacion_fiesta: list[str]
    acceso: list[str]
    pool: list[str]
    rol_participante: list[str]


class AdminCatalogosOut(BaseSchema):
    """The filter option lists of the active event."""

    evento_id: str
    evento_nombre: str
    disciplinas: list[AdminCatalogoItemOut]
    paquetes: list[AdminCatalogoPaqueteOut]
    promociones: list[AdminCatalogoItemOut]
    categorias: list[AdminCatalogoItemOut]
    puntos_acceso: list[str]
    estados: AdminEstadosCatalogosOut


__all__ = [
    "AdminCatalogoItemOut",
    "AdminCatalogoPaqueteOut",
    "AdminEstadosCatalogosOut",
    "AdminCatalogosOut",
]
