"""Re-export de los modelos del módulo `salesianos_fest`."""

from modules.salesianos_fest.domain.models.capacidad import (
    ActivacionCapacidad,
    BeneficioConcedido,
)
from modules.salesianos_fest.domain.models.catalogo import (
    Disciplina,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
)
from modules.salesianos_fest.domain.models.inscripcion import Equipo, Inscripcion
from modules.salesianos_fest.domain.models.participacion import Participacion

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
