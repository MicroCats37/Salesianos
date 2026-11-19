"""`CatalogoController` — superficie HTTP del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0`
Ledger: `SH-05` §1.3 (`RT-IN-12`, `RT-IN-13`) — **provisionales**: existen
cuando A0 registre este controller en `config/api.py` (FR-07 §3.1.2).

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.
"""

from uuid import UUID

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from ninja import Query

from core.responses import ApiResponse, success_response
from modules.salesianos_fest.domain.services.orchestrators.catalogo_orchestrator import (
    CatalogoOrchestrator,
)
from modules.salesianos_fest.presentation.presenters.catalogo_presenter import (
    CatalogoPresenter,
)
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import (
    CatalogoDisciplinasOut,
    CatalogoPaquetesOut,
)


@api_controller("/catalogo", tags=["Catálogo de inscripción"])
class CatalogoController:
    """Catálogo público de paquetes y disciplinas de la edición."""

    @inject
    def __init__(self, orchestrator: CatalogoOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/paquetes",
        response={200: ApiResponse[CatalogoPaquetesOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Paquetes comprables de la edición del alcance.",
    )
    async def listar_paquetes(
        self,
        request,
        edicion_id: UUID = Query(
            None,
            description=(
                "Edición del alcance. Si se omite, se resuelve por el orden "
                "congelado de edición."
            ),
        ),
    ):
        """Route: GET /api/catalogo/paquetes

        El catálogo es REAL y está acotado por EDICIÓN (`RN-E01`). Un paquete
        sin precio vigente NO aparece: no hay precio de reserva
        (`FL-01` paso 3).
        """
        result = await self.orchestrator.listar_paquetes(edicion_id)
        return success_response(
            CatalogoPresenter.present_paquetes(result),
            message="Catálogo de paquetes consultado correctamente.",
        )

    @route.get(
        "/disciplinas",
        response={200: ApiResponse[CatalogoDisciplinasOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Disciplinas activas de la edición del alcance.",
    )
    async def listar_disciplinas(
        self,
        request,
        edicion_id: UUID = Query(
            None,
            description=(
                "Edición del alcance. Si se omite, se resuelve por el orden "
                "congelado de edición."
            ),
        ),
    ):
        """Route: GET /api/catalogo/disciplinas

        Sólo se publican las disciplinas `ACTIVA` de la edición del alcance.
        """
        result = await self.orchestrator.listar_disciplinas(edicion_id)
        return success_response(
            CatalogoPresenter.present_disciplinas(result),
            message="Catálogo de disciplinas consultado correctamente.",
        )


__all__ = ["CatalogoController"]
