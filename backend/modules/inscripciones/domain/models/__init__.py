"""Models package — Django models re-exported by domain."""

from .disciplina import Disciplina, Categoria
from .paquete import Paquete, PaqueteDisciplina
from .evento import Evento
from .promocion import Promocion
from .inscripcion import Inscripcion, InscripcionDelegado
from .equipo import EquipoInscrito, ParticipacionDisciplina, ParticipanteInscripcion

__all__ = [
    "Disciplina",
    "Categoria",
    "Paquete",
    "PaqueteDisciplina",
    "Evento",
    "Promocion",
    "Inscripcion",
    "InscripcionDelegado",
    "EquipoInscrito",
    "ParticipacionDisciplina",
    "ParticipanteInscripcion",
]
