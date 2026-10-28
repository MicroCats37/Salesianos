"""
PersonaResolucionController — resolución EXACTA de una identidad registrada.

Controlador HTTP delgado: parsea la entrada, delega al orquestador y
retorna el resultado formateado por el presenter
(`contract/django-app-architecture-contract.md` §4.8). Sin `if`, sin ORM y
sin respuestas de error manuales: el error tipado lo traduce el catálogo
público de `core/exceptions.py`.

Autorización: la resolución exige una SESIÓN (JWTAuth + IsAuthenticated). Un
visitante anónimo recibe 401 y nunca llega a la consulta.

Rutas:
  GET /personas/resolver?tipo_documento=DNI&numero_documento=12345678
"""

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.usuarios.domain.services.orchestrators.persona_resolucion_orchestrator import (
    PersonaResolucionOrchestrator,
)
from modules.usuarios.presentation.presenters.persona_resolucion_presenter import (
    PersonaResolucionPresenter,
)
from modules.usuarios.presentation.schemas.persona_resolucion_schemas import (
    PersonaResueltaOut,
)


@api_controller("/personas", tags=["Personas"], permissions=[AllowAny])
class PersonaResolucionController:
    """
    Controlador de la resolución exacta de una `Persona` ya registrada.

    NO es el lookup externo de documento: aquel consulta RENIEC/SUNAT y es
    público. Este resuelve el id INTERNO de una persona que ya existe en la
    aplicación, y por eso exige una sesión.
    """

    @inject
    def __init__(
        self,
        orchestrator: PersonaResolucionOrchestrator,
        presenter: PersonaResolucionPresenter,
    ):
        self.orchestrator = orchestrator
        self.presenter = presenter

    @route.get(
        "/resolver",
        response={200: ApiResponse[PersonaResueltaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def resolver_persona(
        self,
        tipo_documento: str = Query(
            ...,
            max_length=3,
            description="Tipo de documento: DNI, CE o PAS.",
        ),
        numero_documento: str = Query(
            ...,
            min_length=1,
            max_length=20,
            description="Número de documento de la persona registrada.",
        ),
    ):
        """
        Resuelve la `Persona` que corresponde EXACTAMENTE al documento.

        Route: GET /api/personas/resolver?tipo_documento=DNI&numero_documento=12345678
        Auth: requiere sesión (JWTAuth + IsAuthenticated).

        La coincidencia es EXACTA: `(tipo_documento, numero_documento)`. No
        hay búsqueda difusa ni listado, y la consulta NUNCA crea ni modifica
        una `Persona`.

        Raises:
            PersonaNoEncontradaError: no hay una `Persona` registrada con ese
                documento exacto (404 con el código público estable).
        """
        result = await self.orchestrator.resolver_persona(
            tipo_documento,
            numero_documento,
        )
        return success_response(
            self.presenter.present_persona(result),
            message="Persona encontrada correctamente.",
        )


__all__ = ["PersonaResolucionController"]
