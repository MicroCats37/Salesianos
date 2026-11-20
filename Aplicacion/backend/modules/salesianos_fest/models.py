"""Re-export puro de los modelos del módulo `salesianos_fest`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta desde `domain/models/`.
"""

from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    ActivacionPase,
    BeneficioConcedido,
    CompraPase,
    CortesiaPase,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Pase,
    PaseBeneficiario,
    PasePrecio,
    Participacion,
)

__all__ = [
    "ActivacionCapacidad",
    "ActivacionPase",
    "BeneficioConcedido",
    "CompraPase",
    "CortesiaPase",
    "Disciplina",
    "Equipo",
    "Inscripcion",
    "Paquete",
    "PaqueteBeneficio",
    "PaqueteDisciplina",
    "PaquetePrecio",
    "Pase",
    "PaseBeneficiario",
    "PasePrecio",
    "Participacion",
]
