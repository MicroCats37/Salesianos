"""Domain selectors for salesianos_fest module."""
from .disciplina_selector import DisciplinaSelector
from .promocion_selector import PromocionSelector
from .categoria_selector import CategoriaSelector
from .paquete_selector import PaqueteSelector
from .inscripcion_selector import InscripcionSelector
from .equipo_selector import EquipoSelector
from .participacion_selector import ParticipacionSelector
from .compra_selector import CompraSelector
from .asignacion_selector import AsignacionSelector
from .acreditacion_selector import AcreditacionSelector
from .control_acceso_selector import ControlAccesoSelector
from .aceptacion_inscripcion_selector import AceptacionInscripcionSelector

__all__ = [
    "DisciplinaSelector",
    "PromocionSelector",
    "CategoriaSelector",
    "PaqueteSelector",
    "InscripcionSelector",
    "EquipoSelector",
    "ParticipacionSelector",
    "CompraSelector",
    "AsignacionSelector",
    "AcreditacionSelector",
    "ControlAccesoSelector",
    "AceptacionInscripcionSelector",
]
