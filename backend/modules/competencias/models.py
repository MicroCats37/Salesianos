"""Re-export from domain/models/ — pure re-export, never logic."""
from .domain.models import Competencia, CompetenciaEquipo, Ronda, Encuentro

__all__ = [
    "Competencia",
    "CompetenciaEquipo",
    "Ronda",
    "Encuentro",
]
