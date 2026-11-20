"""Resultados (DTO de salida) del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Dataclasses planas: el presenter los proyecta a las formas HTTP y no
recalcula nada. Cada resultado lleva YA la prosa que se publica, para que el
cliente nunca invente la etiqueta de un estado ni de una incidencia.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class ResumenMetricaResultado:
    """Una cifra del resumen operativo."""

    codigo: str
    etiqueta: str
    descripcion: str
    valor: int


@dataclass(frozen=True)
class ResumenAccionResultado:
    """La acción concreta que resuelve una incidencia.

    `href` es la vista operativa FILTRADA: una ruta del panel que EXISTE y un
    filtro DECLARADO (`FiltroResumen`).
    """

    codigo: str
    etiqueta: str
    href: str


@dataclass(frozen=True)
class ResumenIncidenciaResultado:
    """Un problema visible del resumen y su acción autorizada."""

    codigo: str
    etiqueta: str
    descripcion: str
    cantidad: int
    vista: str
    filtro: str
    filtro_valor: str
    accion_codigo: str
    accion_etiqueta: str


@dataclass(frozen=True)
class ResumenOperativoResultado:
    """El resumen completo de UNA edición."""

    edicion_id: str
    edicion_nombre: str
    edicion_estado: str
    metricas: List[ResumenMetricaResultado] = field(default_factory=list)
    incidencias: List[ResumenIncidenciaResultado] = field(default_factory=list)


@dataclass(frozen=True)
class AuditoriaItemResultado:
    """Un acta de auditoría, ya saneada para publicarse."""

    id: str
    edicion_id: Optional[str]
    actor: str
    accion: str
    entidad: str
    entidad_id: str
    motivo: str
    registrado_en: datetime


@dataclass(frozen=True)
class AuditoriaListadoResultado:
    """Una página de actas de auditoría."""

    items: List[AuditoriaItemResultado] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


__all__ = [
    "AuditoriaItemResultado",
    "AuditoriaListadoResultado",
    "ResumenAccionResultado",
    "ResumenIncidenciaResultado",
    "ResumenMetricaResultado",
    "ResumenOperativoResultado",
]
