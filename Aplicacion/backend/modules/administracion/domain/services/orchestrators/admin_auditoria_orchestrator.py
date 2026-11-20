"""`AdminAuditoriaOrchestrator` — la fachada async del acta transversal.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Dos operaciones y ninguna más:

- `listar_auditoria` — la lectura paginada del acta.
- `registrar_accion` — la escritura del acta de una acción sensible.

La escritura exige el motivo (422 si falta) y sanea el contexto. El
orquestador no inventa reglas: delega en el servicio y en el selector.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.administracion.domain.results.admin_resultados import (
    AuditoriaListadoResultado,
)
from modules.administracion.domain.selectors.admin_auditoria_selector import (
    AdminAuditoriaSelector,
)
from modules.administracion.domain.services.core.admin_auditoria_service import (
    AdminAuditoriaService,
)


class AdminAuditoriaOrchestrator:
    """Fachada async del acta de auditoría."""

    @inject
    def __init__(
        self,
        selector: AdminAuditoriaSelector,
        service: AdminAuditoriaService,
    ):
        self.selector = selector
        self.service = service

    async def listar_auditoria(
        self,
        edicion_id=None,
        accion=None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditoriaListadoResultado:
        """Las actas de la página pedida."""
        return await sync_to_async(self.selector.listar)(
            edicion_id=edicion_id,
            accion=accion,
            page=page,
            page_size=page_size,
        )

    async def registrar_accion(
        self,
        actor,
        accion: str,
        entidad: str,
        motivo: str,
        edicion_id=None,
        entidad_id: str = "",
        datos=None,
    ):
        """Registra el acta de una acción sensible."""
        return await sync_to_async(self.service.registrar)(
            actor,
            accion,
            entidad,
            motivo,
            edicion_id=edicion_id,
            entidad_id=entidad_id,
            datos=datos,
        )


__all__ = ["AdminAuditoriaOrchestrator"]
