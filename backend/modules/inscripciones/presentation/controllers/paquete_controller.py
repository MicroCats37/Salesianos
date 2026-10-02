"""PaqueteController — catalog endpoints for paquetes."""

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject

from core.responses import ApiResponse, success_response
from modules.inscripciones.presentation.schemas.paquete_schemas import (
    PaqueteDetalleOut,
    PaqueteDisciplinaOut,
    PaqueteOut,
)
from modules.inscripciones.presentation.presenters.paquete_presenter import (
    present_paquete,
)
from modules.inscripciones.domain.services.core.paquete_service import PaqueteService
from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector


@api_controller("/inscripciones/paquetes", tags=["Catálogos"], permissions=[AllowAny])
class PaqueteController:
    """
    Controlador para listar paquetes disponibles.

    Endpoints públicos de solo lectura.

    Rutas:
      GET /inscripciones/paquetes/                          -> listar_paquetes
      GET /inscripciones/paquetes/{paquete_id}/disciplinas  -> listar_disciplinas_de_paquete
    """

    @inject
    def __init__(self, paquete_svc: PaqueteService, selector: InscripcionSelector):
        self.paquete_svc = paquete_svc
        self.selector = selector

    @route.get("/", response={200: ApiResponse[list[PaqueteOut]]}, auth=None)
    def listar_paquetes(self):
        """
        Listar todos los paquetes activos.

        Route: GET /api/inscripciones/paquetes/
        Auth: public (no JWT).
        Returns: lista de paquetes con precios, validez y `cantidad_maxima_equipos`
                 (calculada según el modo de disciplinas).
        """
        paquetes = self.paquete_svc.listar_activos()
        data = [present_paquete(p) for p in paquetes]
        return success_response(data)

    @route.get("/{paquete_id}/disciplinas", response={200: ApiResponse[list[PaqueteDisciplinaOut]]}, auth=None)
    def listar_disciplinas_de_paquete(self, paquete_id: str):
        """
        Listar disciplinas incluidas en un paquete.

        Route: GET /api/inscripciones/paquetes/{paquete_id}/disciplinas
        Auth: public (no JWT).
        Returns: lista de disciplinas que se pueden inscribir con este paquete.
        """
        disciplinas = self.selector.listar_disciplinas_de_paquete(paquete_id)
        data = [
            PaqueteDisciplinaOut(
                disciplina_id=str(d.id),
                disciplina_nombre=d.nombre,
                disciplina_sigla=d.sigla,
                min_jugadores=d.min_jugadores,
                max_jugadores=d.max_jugadores,
            )
            for d in disciplinas
        ]
        return success_response(data)
