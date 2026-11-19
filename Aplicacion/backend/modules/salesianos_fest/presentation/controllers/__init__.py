"""Controllers del módulo `salesianos_fest`.

El REGISTRO permanente en `config/api.py` es de A0 (petición A0-03 de este
paquete). Hasta entonces, sus rutas NO existen: código escrito y no
registrado es código muerto (`FR-07` §3.1.2).
"""

from modules.salesianos_fest.presentation.controllers.catalogo_controller import (
    CatalogoController,
)
from modules.salesianos_fest.presentation.controllers.inscripcion_controller import (
    InscripcionController,
)

__all__ = ["CatalogoController", "InscripcionController"]
