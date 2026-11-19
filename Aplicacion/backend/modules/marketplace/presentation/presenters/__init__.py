"""Presenters del módulo `marketplace`.

Contract: `contract/api-wrapper-presenter-contract.md` §3

Un presenter es un TRANSFORMADOR PURO: recibe el result object del dominio y
devuelve el wrapper HTTP. No consulta la base de datos, no decide estados y
no construye mensajes de error.
"""

from modules.marketplace.presentation.presenters.pedido_presenter import (
    PedidoPresenter,
    PedidoSeguimientoPresenter,
)

__all__ = [
    "PedidoPresenter",
    "PedidoSeguimientoPresenter",
]
