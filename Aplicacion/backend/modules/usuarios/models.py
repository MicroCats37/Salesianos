"""Re-export PURO de los modelos del módulo (sin lógica).

`contract/django-app-architecture-contract.md` §4.1: este archivo no puede
contener lógica; sólo re-exporta desde `domain/models/`.
"""

from .domain.models import Persona, Usuario

__all__ = ["Persona", "Usuario"]
