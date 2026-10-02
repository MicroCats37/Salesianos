"""Core services — sync business logic services."""

from .disciplina_service import DisciplinaService
from .paquete_service import PaqueteService
from .evento_service import EventoService
from .inscripcion_service import InscripcionService
from .equipo_service import EquipoService
from .participacion_service import ParticipacionService
from .participante_service import ParticipanteService
from .validators import (
    validar_roster_equipo,
    validar_disciplina_en_paquete,
    validar_r11_prevent_duplicado,
    validar_equipo_duplicado,
    calcular_cupo_paquete,
    validar_cupo_paquete,
    validar_delegado_es_elegible,
    validar_consistencia_equipo_participacion,
)
