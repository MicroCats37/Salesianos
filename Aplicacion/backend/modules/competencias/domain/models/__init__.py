"""Modelos del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.2

Este archivo sólo RE-EXPORTA: la definición de cada modelo vive en su propio
archivo, agrupado por su relación semántica (`base`, `competencia`,
`competencia_equipo`, `ronda`, `encuentro`, `auditoria`).
"""

from modules.competencias.domain.models.auditoria import (
    AccionAuditada,
    AuditoriaOperacion,
)
from modules.competencias.domain.models.base import CompetenciaBaseModel
from modules.competencias.domain.models.competencia import Competencia
from modules.competencias.domain.models.competencia_equipo import CompetenciaEquipo
from modules.competencias.domain.models.encuentro import Encuentro
from modules.competencias.domain.models.ronda import Ronda
from modules.competencias.domain.models.torneo import (
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
)

__all__ = [
    "AccionAuditada",
    "AuditoriaOperacion",
    "Competencia",
    "CompetenciaBaseModel",
    "CompetenciaEquipo",
    "Encuentro",
    "EquipoTorneo",
    "GrupoTorneo",
    "PartidoTorneo",
    "Ronda",
]
