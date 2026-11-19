"""Re-export puro de los modelos del módulo `salesianos_fest`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta desde `domain/models/`.
"""

from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    BeneficioConcedido,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Participacion,
)

__all__ = [
    "ActivacionCapacidad",
    "BeneficioConcedido",
    "Disciplina",
    "Equipo",
    "Inscripcion",
    "Paquete",
    "PaqueteBeneficio",
    "PaqueteDisciplina",
    "PaquetePrecio",
    "Participacion",
]
