"""Controllers of the administracion module."""

from modules.administracion.presentation.controllers.admin_fundacion_controller import (
    AdminFundacionController,
)
from modules.administracion.presentation.controllers.admin_inscripcion_controller import (
    AdminInscripcionController,
)
from modules.administracion.presentation.controllers.admin_operacion_controller import (
    AdminOperacionController,
)
from modules.administracion.presentation.controllers.admin_pago_controller import (
    AdminPagoController,
)
from modules.administracion.presentation.controllers.admin_resumen_controller import (
    AdminResumenController,
)
from modules.administracion.presentation.controllers.admin_usuario_controller import (
    AdminUsuarioController,
)

__all__ = [
    "AdminFundacionController",
    "AdminResumenController",
    "AdminInscripcionController",
    "AdminPagoController",
    "AdminOperacionController",
    "AdminUsuarioController",
]
