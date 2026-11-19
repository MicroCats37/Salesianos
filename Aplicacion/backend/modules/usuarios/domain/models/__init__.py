"""Re-export de los modelos del dominio (sin lógica)."""

from .persona import Persona
from .usuario import Usuario

__all__ = ["Persona", "Usuario"]
