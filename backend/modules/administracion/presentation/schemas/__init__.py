"""HTTP schemas of the administracion module."""

from modules.administracion.presentation.schemas.admin_acreditacion_schemas import (
    AdminAccesoListItemOut,
    AdminAcreditacionDetailOut,
    AdminAcreditacionListItemOut,
)
from modules.administracion.presentation.schemas.admin_fundacion_schemas import (
    AdminHealthOut,
)
from modules.administracion.presentation.schemas.admin_inscripcion_schemas import (
    AdminAceptacionListItemOut,
    AdminAsignacionListItemOut,
    AdminEquipoDetalleOut,
    AdminEquipoListItemOut,
    AdminInscripcionDetailOut,
    AdminInscripcionListItemOut,
    AdminParticipacionListItemOut,
    AdminParticipanteListItemOut,
    AdminSaldoOut,
)
from modules.administracion.presentation.schemas.admin_pago_schemas import (
    AdminPagoDetailOut,
    AdminPagoListItemOut,
    AdminTransaccionListItemOut,
)
from modules.administracion.presentation.schemas.admin_resumen_schemas import (
    AdminResumenOut,
)
from modules.administracion.presentation.schemas.admin_catalogos_schemas import (
    AdminCatalogosOut,
)
from modules.administracion.presentation.schemas.admin_usuario_schemas import (
    AdminUsuarioDetailOut,
    AdminUsuarioInscripcionOut,
    AdminUsuarioListItemOut,
)

__all__ = [
    "AdminHealthOut",
    "AdminResumenOut",
    "AdminCatalogosOut",
    "AdminInscripcionListItemOut",
    "AdminInscripcionDetailOut",
    "AdminEquipoListItemOut",
    "AdminEquipoDetalleOut",
    "AdminParticipanteListItemOut",
    "AdminParticipacionListItemOut",
    "AdminAsignacionListItemOut",
    "AdminAceptacionListItemOut",
    "AdminSaldoOut",
    "AdminPagoListItemOut",
    "AdminPagoDetailOut",
    "AdminTransaccionListItemOut",
    "AdminAcreditacionListItemOut",
    "AdminAcreditacionDetailOut",
    "AdminAccesoListItemOut",
    "AdminUsuarioListItemOut",
    "AdminUsuarioDetailOut",
    "AdminUsuarioInscripcionOut",
]
