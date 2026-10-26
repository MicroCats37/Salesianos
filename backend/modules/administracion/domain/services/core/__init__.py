"""
Core services (sync, no `transaction.atomic`) of the administracion module.

- `AdminPaginacionService` owns the canonical pagination, search and ordering
  rules of the administrative surface.
- `AdminConsultaService` composes the operational aggregates and the filter
  catalogs out of the selectors of the owning modules.
- `AdminEventoActivoService` resolves the ACTIVE event — the scope of every
  administrative read.
- `AdminOperacionService` validates the filter values, builds the canonical
  pagination parameters and composes the operational tables (A3–A14).
"""

from modules.administracion.domain.services.core.admin_consulta_service import (
    AdminConsultaService,
)
from modules.administracion.domain.services.core.admin_evento_activo_service import (
    AdminEventoActivoService,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)

__all__ = [
    "AdminConsultaService",
    "AdminEventoActivoService",
    "AdminOperacionService",
]
