"""Puertos (interfaces) del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.10
"""

from modules.marketplace.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.marketplace.domain.ports.comercio import ICommerceMarketplaceService
from modules.marketplace.domain.ports.titularidad import ITitularidadActorService

__all__ = [
    "IAlcanceEdicion",
    "ICommerceMarketplaceService",
    "ITitularidadActorService",
]
