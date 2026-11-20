"""Controllers del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Los controllers son delgados: parsean, delegan al orquestador y devuelven
el éxito formateado por el presenter
(`contract/django-app-architecture-contract.md` §4.8).
"""

from .admin_controller import AdminController
from .admin_equipo_controller import AdminEquipoController
from .admin_inscripcion_controller import AdminInscripcionController
from .admin_pago_controller import AdminPagoController
from .admin_participante_controller import AdminParticipanteController
from .admin_persona_controller import AdminPersonaController

__all__ = [
    "AdminController",
    "AdminEquipoController",
    "AdminInscripcionController",
    "AdminPagoController",
    "AdminParticipanteController",
    "AdminPersonaController",
]
