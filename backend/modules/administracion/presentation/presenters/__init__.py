"""Presenters of the administracion module."""

from modules.administracion.presentation.presenters.admin_acreditacion_presenter import (
    AdminAcreditacionPresenter,
)
from modules.administracion.presentation.presenters.admin_fundacion_presenter import (
    AdminFundacionPresenter,
)
from modules.administracion.presentation.presenters.admin_inscripcion_presenter import (
    AdminInscripcionPresenter,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.presenters.admin_pago_presenter import (
    AdminPagoPresenter,
)
from modules.administracion.presentation.presenters.admin_resumen_presenter import (
    AdminResumenPresenter,
)
from modules.administracion.presentation.presenters.admin_catalogos_presenter import (
    AdminCatalogosPresenter,
)
from modules.administracion.presentation.presenters.admin_usuario_presenter import (
    AdminUsuarioPresenter,
)

__all__ = [
    "AdminFundacionPresenter",
    "AdminPaginacionPresenter",
    "AdminResumenPresenter",
    "AdminCatalogosPresenter",
    "AdminInscripcionPresenter",
    "AdminPagoPresenter",
    "AdminAcreditacionPresenter",
    "AdminUsuarioPresenter",
]
