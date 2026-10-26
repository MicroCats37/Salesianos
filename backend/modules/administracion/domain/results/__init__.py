"""Internal result DTOs of the administracion module."""

from modules.administracion.domain.results.admin_fundacion_results import (
    AdminFundacionResult,
)
from modules.administracion.domain.results.admin_catalogos_results import (
    AdminCatalogosResult,
)
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.domain.results.admin_resumen_results import (
    AdminResumenResult,
)

__all__ = [
    "AdminFundacionResult",
    "AdminCatalogosResult",
    "AdminListadoResult",
    "AdminResumenResult",
]
