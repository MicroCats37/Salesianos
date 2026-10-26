"""
Domain selectors of the administracion module.

The administrative queries read the data of the business modules through the
SELECTORS OF THE OWNING MODULES (`modules.eventos.EventoSelector`,
`modules.usuarios.UsuarioSelector` / `PersonaSelector`,
`modules.salesianos_fest.ControlAccesoSelector` /
`AceptacionInscripcionSelector`).

The `Admin*Selector` classes live here because the OPERATIONAL TABLES span
SEVERAL modules at once: they read the owning modules' models through their
`domain/models` re-exports and never import another module's `presentation/`
layer (`contract/api-wrapper-presenter-contract.md` §1).

Every one of them is READ-ONLY: the administrative area has no write path.
"""

from modules.administracion.domain.selectors.admin_acreditacion_selector import (
    AdminAcreditacionSelector,
)
from modules.administracion.domain.selectors.admin_equipo_selector import (
    AdminEquipoSelector,
)
from modules.administracion.domain.selectors.admin_inscripcion_selector import (
    AdminInscripcionSelector,
)
from modules.administracion.domain.selectors.admin_pago_selector import (
    AdminPagoSelector,
)
from modules.administracion.domain.selectors.admin_participante_selector import (
    AdminParticipanteSelector,
)
from modules.administracion.domain.selectors.admin_resumen_selector import (
    AdminResumenSelector,
)
from modules.administracion.domain.selectors.admin_usuario_selector import (
    AdminUsuarioSelector,
)

__all__ = [
    "AdminResumenSelector",
    "AdminInscripcionSelector",
    "AdminPagoSelector",
    "AdminEquipoSelector",
    "AdminParticipanteSelector",
    "AdminAcreditacionSelector",
    "AdminUsuarioSelector",
]
