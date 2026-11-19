"""
`PersonaController` — superficie HTTP de la identidad.

Freeze: `FREEZE-ID-1.0.0` · `FREEZE-PS-1.0.0` · ledger `RT-ID-01`, `RT-ID-02`,
`RT-ID-03`.

El controller es "SAGRADO" (`contract/PLAN_REFACTORIZACION.md` §1.A): parsea
la entrada, llama al orquestador y devuelve el éxito formateado por el
presenter. Ni una rama, ni ORM, ni respuestas de error manuales: los errores
los traducen las excepciones de dominio con código estable a través del
catálogo público de `core/exceptions.py`.

Autorización:

- `RT-ID-01` es PÚBLICA (`auth=None` + `AllowAny`): es el autocompletado del
  documento, no una superficie de datos personales del festival.
- `RT-ID-02` y `RT-ID-03` exigen SESIÓN (`JWTAuth` + `IsAuthenticated`). Un
  cliente anónimo recibe 401 y nunca llega a la consulta.

El REGISTRO de este controller en `config/api.py` es de A0
(`config/api.py` es archivo compartido). La clase está lista para registrarse.
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.usuarios.domain.schemas import PersonaConfirmarData
from modules.usuarios.domain.services.orchestrators.persona_orchestrator import (
    PersonaOrchestrator,
)
from modules.usuarios.presentation.presenters.persona_presenter import (
    PersonaBusquedaPresenter,
    PersonaConfirmarPresenter,
    PersonaResolverPresenter,
)
from modules.usuarios.presentation.schemas.persona_schemas import (
    DocumentoConsultaOut,
    PersonaConfirmarIn,
    PersonaOut,
    PersonaResueltaOut,
    PersonaResolverIn,
)


@api_controller("/personas", tags=["Personas"])
class PersonaController:
    """Identidad civil: consulta, resolución y confirmación."""

    @inject
    def __init__(
        self,
        orchestrator: PersonaOrchestrator,
        presenter_busqueda: PersonaBusquedaPresenter,
        presenter_resolver: PersonaResolverPresenter,
        presenter_confirmar: PersonaConfirmarPresenter,
    ):
        self.orchestrator = orchestrator
        self.presenter_busqueda = presenter_busqueda
        self.presenter_resolver = presenter_resolver
        self.presenter_confirmar = presenter_confirmar

    @route.get(
        "/busqueda/{documento}",
        response={200: ApiResponse[DocumentoConsultaOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Consulta un documento en la fuente externa de identidad.",
    )
    async def buscar_documento(self, request, documento: str):
        """Consulta un documento en la fuente externa.

        Route: GET /api/personas/busqueda/{documento}
        Auth: pública.

        La fuente decide qué tipo de documento reconoce. NO devuelve el id
        interno de la aplicación: sólo la identidad civil que publica la
        fuente.
        """
        result = await self.orchestrator.consultar_externa(documento)
        return success_response(
            self.presenter_busqueda.present_consulta(result),
            message="Documento consultado correctamente.",
        )

    @route.post(
        "/resolver",
        response={200: ApiResponse[PersonaResueltaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Resuelve una identidad por documento (local primero).",
    )
    async def resolver(self, request, payload: PersonaResolverIn):
        """Resuelve una identidad por documento, buscando primero en local.

        Route: POST /api/personas/resolver
        Auth: requiere sesión.

        Si la persona ya está registrada, la respuesta trae su `persona_id`
        y la fuente externa NO se consulta. Si no existe, la respuesta trae
        los datos precargados con `persona_id` nulo: la identidad todavía NO
        está persistida.

        Esta ruta NO autoriza ninguna operación: resolver un documento no
        da acceso a la cuenta ni al historial de otra persona (`RN-U04`).
        """
        result = await self.orchestrator.resolver(
            payload.tipo_documento,
            payload.numero_documento,
        )
        return success_response(
            self.presenter_resolver.present_resolucion(result),
            message="Identidad resuelta correctamente.",
        )

    @route.post(
        "/confirmar",
        response={200: ApiResponse[PersonaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Confirma y persiste una identidad.",
    )
    async def confirmar(self, request, payload: PersonaConfirmarIn):
        """Confirma la identidad y la persiste.

        Route: POST /api/personas/confirmar
        Auth: requiere sesión.

        Es la operación real que persiste la `Persona`. NO crea una cuenta:
        el nacimiento de cuenta es explícito y aparte (`FR-03` §1.2).

        Si el documento ya está vinculado a una cuenta, la respuesta es 409
        `PERSONA_DUPLICADA`: la identidad no se reescribe ni se duplica.
        """
        result = await self.orchestrator.confirmar(
            PersonaConfirmarData(
                tipo_documento=payload.tipo_documento,
                numero_documento=payload.numero_documento,
                nombres=payload.nombres,
                apellidos=payload.apellidos or "",
                genero=payload.genero or "",
            ),
        )
        return success_response(
            self.presenter_confirmar.present_persona(result),
            message="Identidad registrada correctamente.",
        )


__all__ = ["PersonaController"]
