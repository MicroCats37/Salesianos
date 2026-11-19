"""Puertos (interfaces) del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.10

`IAlcanceEdicion` es el ÚNICO puerto que el módulo consume de fuera: la
resolución del alcance de edición (FR-02 §2.2). La implementación concreta
vive en `infrastructure/services/` para que el dominio no dependa del
módulo que provee el dato.
"""

from abc import ABC, abstractmethod


class IAlcanceEdicion(ABC):
    """Resolución del alcance de edición para el marketplace."""

    @abstractmethod
    def resolver_actual(self):
        """La edición vigente según el orden congelado de FR-02 §2.2."""
        raise NotImplementedError

    @abstractmethod
    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """La edición indicada por identificador, sin fallback alguno."""
        raise NotImplementedError


__all__ = ["IAlcanceEdicion"]
