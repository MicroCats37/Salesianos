"""Controllers del módulo `competencias`."""

from modules.competencias.presentation.controllers.competencias_controller import (
    CompetenciasController,
)
from modules.competencias.presentation.controllers.competencias_publico_controller import (
    CompetenciasPublicoController,
)
from modules.competencias.presentation.controllers.mis_partidos_controller import (
    MisPartidosController,
)

__all__ = [
    "CompetenciasController",
    "CompetenciasPublicoController",
    "MisPartidosController",
]
