"""`CotizacionController` — superficie HTTP de la cotización de un paquete.

Change: `restore-registration-promotion-catalog-flow` (2026-11-20)

Ledger: ruta PROVISIONAL — A0 tiene que registrar este controller en
`config/api.py` (`FR-07` §3.1.2).

La cotización es un cálculo de LECTURA contra el catálogo vigente (`RN-C02`):
el cliente pregunta por un paquete y una cantidad y el servidor responde con
el precio UNITARIO, el total que deriva y el token de concurrencia del
precio. NO se persiste: pertenece a la sesión del comprador.

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.salesianos_fest.domain.schemas.catalogo_schemas import CotizacionData
from modules.salesianos_fest.domain.services.orchestrators.catalogo_orchestrator import (
    CatalogoOrchestrator,
)
from modules.salesianos_fest.presentation.presenters.catalogo_presenter import (
    CatalogoPresenter,
)
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import CotizacionOut
from modules.salesianos_fest.presentation.schemas.cotizacion_schemas import CotizacionIn


@api_controller("/cotizaciones", tags=["Cotizaciones de inscripción"])
class CotizacionController:
    """Cotización de un paquete para una cantidad de participantes."""

    @inject
    def __init__(self, orchestrator: CatalogoOrchestrator):
        self.orchestrator = orchestrator

    @route.post(
        "",
        response={200: ApiResponse[CotizacionOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Cotiza un paquete para una cantidad de participantes.",
    )
    async def cotizar(self, request, payload: CotizacionIn):
        """Route: POST /api/cotizaciones

        El precio es el vigente del catálogo y el total lo deriva el servidor
        como `cantidad × precio_unitario`: el cliente NO envía ningún
        importe (`RN-C02`).

        La cantidad se contrasta contra el mínimo COMERCIAL del paquete: no
        hay un máximo global de participantes.

        El `version` que devuelve es el token de concurrencia del precio: el
        alta lo devuelve para que el servidor detecte que el catálogo se movió
        entre la cotización y la confirmación.
        """
        data = CotizacionData(
            paquete_id=payload.paquete_id,
            cantidad=payload.cantidad,
        )
        result = await self.orchestrator.cotizar(data.paquete_id, data.cantidad)
        return success_response(
            CatalogoPresenter.present_cotizacion(result),
            message="Cotización calculada correctamente.",
        )


__all__ = ["CotizacionController"]
