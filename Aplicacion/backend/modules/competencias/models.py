"""Re-export puro de los modelos del módulo `competencias`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta desde `domain/models/`.
"""

from modules.competencias.domain.models import (
    AccionAuditada,
    AuditoriaOperacion,
    Competencia,
    CompetenciaBaseModel,
    CompetenciaEquipo,
    Encuentro,
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
    Ronda,
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
