"""Presenters del módulo `patrocinadores`.

Contract: `contract/api-wrapper-presenter-contract.md` §3

Un presenter es un TRANSFORMADOR PURO: recibe el result object del dominio y
devuelve el wrapper HTTP. No consulta la base de datos, no decide estados y
no construye mensajes de error.
"""

from modules.patrocinadores.presentation.presenters.patrocinadores_presenter import (
    PatrocinadorPresenter,
)

__all__ = [
    "PatrocinadorPresenter",
]
