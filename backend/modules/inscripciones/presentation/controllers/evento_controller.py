"""EventoController — catalog endpoints for eventos."""

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject

from core.responses import ApiResponse, success_response
from modules.inscripciones.presentation.schemas.evento_schemas import EventoOut
from modules.inscripciones.domain.services.core.evento_service import EventoService


@api_controller("/inscripciones/eventos", tags=["Catálogos"], permissions=[AllowAny])
class EventoController:
    """
    Controlador para listar eventos activos.

    Endpoints públicos de solo lectura.

    Rutas:
      GET /inscripciones/eventos/ -> listar_eventos
    """

    @inject
    def __init__(self, evento_svc: EventoService):
        self.evento_svc = evento_svc

    @route.get("/", response={200: ApiResponse[list[EventoOut]]}, auth=None)
    def listar_eventos(self):
        """
        Listar todos los eventos activos.

        Route: GET /api/inscripciones/eventos/
        Auth: public (no JWT).
        Returns: lista de eventos disponibles para inscripción.
        """
        eventos = self.evento_svc.listar_activos()
        data = [
            EventoOut(
                id=str(e.id),
                nombre=e.nombre,
                fecha_inicio=e.fecha_inicio,
                fecha_fin=e.fecha_fin,
                esta_activo=e.esta_activo,
            )
            for e in eventos
        ]
        return success_response(data)
