"""Re-export from domain/constants.py — pure re-export, never logic."""
from .domain.constants import (
    EstadoCompetenciaChoices,
    EstadoCompetenciaEquipoChoices,
    EstadoEncuentroChoices,
    EstadoPreSuspensionChoices,
    EstadoRondaChoices,
    SlotDestinoChoices,
)

__all__ = [
    "EstadoCompetenciaChoices",
    "EstadoCompetenciaEquipoChoices",
    "EstadoEncuentroChoices",
    "EstadoPreSuspensionChoices",
    "EstadoRondaChoices",
    "SlotDestinoChoices",
]
