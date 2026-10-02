"""
PersonaBusquedaController — controlador HTTP ligero para endpoint de búsqueda de personas.

Solo delega a PersonaBusquedaOrchestrator y retorna vía PersonaBusquedaPresenter.
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject
from ninja import Path

from core.responses import ApiResponse, success_response
from modules.usuarios.presentation.schemas.persona_busqueda_schemas import DocumentoConsultaOut
from modules.usuarios.presentation.presenters.persona_busqueda_presenter import PersonaBusquedaPresenter
from modules.usuarios.domain.services.orchestrators.persona_busqueda_orchestrator import PersonaBusquedaOrchestrator


@api_controller("/personas", tags=["Personas"], permissions=[AllowAny])
class PersonaBusquedaController:
    """
    Controlador para búsqueda de personas por documento (RENIEC/SUNAT).

    Delega todo formatting de respuesta a PersonaBusquedaPresenter.

    Rutas:
      GET /personas/busqueda/{documento} -> buscar_documento
    """

    @inject
    def __init__(
        self,
        orchestrator: PersonaBusquedaOrchestrator,
        presenter: PersonaBusquedaPresenter,
    ):
        self.orchestrator = orchestrator
        self.presenter = presenter

    @route.get("/busqueda/{documento}", response={200: ApiResponse[DocumentoConsultaOut]}, auth=None)
    async def buscar_documento(
        self,
        documento: str = Path(
            ...,
            min_length=8,
            max_length=11,
            description="Número de documento: DNI (8 dígitos) o RUC (11 dígitos)",
        ),
    ):
        """
        Consulta datos de persona por número de documento (DNI o RUC).

        Route: GET /api/personas/busqueda/{documento}
        Auth: public (no JWT).
        Auto-detecta el tipo de documento:
          - 8 dígitos → DNI (RENIEC)
          - 11 dígitos → RUC (SUNAT)

        Args:
            documento: Número de documento (8 o 11 dígitos).

        Returns:
            Datos del documento (tipo_documento, numero_documento, razon_social).

        Raises:
            ReniecNotFoundError (404): Si el DNI no existe.
            SunatNotFoundError (404): Si el RUC no existe.
        """
        result = await self.orchestrator.buscar_documento(documento)
        return success_response(
            self.presenter.present_documento(result)
        )