"""Esquemas HTTP del resumen operativo.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`
"""

from typing import List

from core.types import BaseSchema


class ResumenMetricaOut(BaseSchema):
    """Una cifra del resumen operativo."""

    codigo: str
    etiqueta: str
    descripcion: str
    valor: int


class ResumenAccionOut(BaseSchema):
    """La acción autorizada que resuelve una incidencia.

    `href` es la vista operativa FILTRADA: una ruta del panel que existe y un
    filtro declarado. El backend NO inventa una ruta que el panel no tiene.
    """

    codigo: str
    etiqueta: str
    href: str


class ResumenIncidenciaOut(BaseSchema):
    """Un problema visible del resumen y su acción."""

    codigo: str
    etiqueta: str
    descripcion: str
    cantidad: int
    accion: ResumenAccionOut


class ResumenOperativoOut(BaseSchema):
    """El resumen completo de UNA edición."""

    edicion_id: str
    edicion_nombre: str
    edicion_estado: str
    metricas: List[ResumenMetricaOut]
    incidencias: List[ResumenIncidenciaOut]


__all__ = [
    "ResumenAccionOut",
    "ResumenIncidenciaOut",
    "ResumenMetricaOut",
    "ResumenOperativoOut",
]
