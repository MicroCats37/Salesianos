"""Core services of the competencias module (sync, no transaction of their own)."""
from .avance_service import AvanceCoreService  # noqa: F401
from .base_service import BaseCoreService  # noqa: F401
from .competencia_service import CompetenciaCoreService  # noqa: F401
from .competencia_equipo_service import (  # noqa: F401
    CompetenciaEquipoCoreService,
)
from .correccion_service import CorreccionCoreService  # noqa: F401
from .encuentro_service import EncuentroCoreService  # noqa: F401
from .programacion_service import ProgramacionCoreService  # noqa: F401
from .resultado_service import ResultadoCoreService  # noqa: F401
from .ronda_service import RondaCoreService  # noqa: F401
