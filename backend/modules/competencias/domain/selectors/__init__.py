"""
Selectors of the competencias module — the read side of the bracket.

A selector LOADS the data and returns domain result DTOs. It never builds an
HTTP schema and it never knows about the presentation layer
(`contract/api-wrapper-presenter-contract.md` §3).

Read-only by construction: no method of these selectors writes.
"""
from modules.competencias.domain.selectors.alcance_selector import (
    AlcanceEventoSelector,
)
from modules.competencias.domain.selectors.competencia_selector import (
    CompetenciaSelector,
)
from modules.competencias.domain.selectors.encuentro_selector import (
    EncuentroSelector,
)

__all__ = [
    "AlcanceEventoSelector",
    "CompetenciaSelector",
    "EncuentroSelector",
]
