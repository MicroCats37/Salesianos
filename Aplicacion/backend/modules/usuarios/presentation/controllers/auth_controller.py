"""
`AuthController` — superficie HTTP de la autenticación y de la sesión.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-ID-1.0.0`.

El controller es "SAGRADO" (`contract/PLAN_REFACTORIZACION.md` §1.A): parsea
la entrada, llama al orquestador y devuelve el éxito formateado por el
presenter. Ni una rama, ni ORM, ni respuestas de error manuales: los errores
los traducen las excepciones de dominio con código estable a través del
catálogo público de `core/exceptions.py`.

Rutas (el prefijo `/api` lo pone el montaje de `config/urls.py`):

| Método | Ruta | Auth | Wrapper |
|---|---|---|---|
| POST | `/api/auth/register` | pública | `ApiResponse[LoginTokenOut]` |
| POST | `/api/auth/login/username` | pública | `ApiResponse[LoginTokenOut]` |
| POST | `/api/auth/login/dni` | pública | `ApiResponse[LoginTokenOut]` |
| POST | `/api/auth/login/email` | pública | `ApiResponse[LoginTokenOut]` |
| GET | `/api/auth/me` | JWT | `ApiResponse[SesionUsuarioOut]` |

El refresco y la verificación de tokens NO están aquí: los sirve el
`NinjaJWTDefaultController` ya registrado en `config/api.py`. Este paquete no
duplica esa lógica.

El REGISTRO de este controller en `config/api.py` es de A0
(`config/api.py` es archivo compartido). La clase está lista para registrarse.
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.usuarios.domain.schemas.persona_schemas import PersonaCreateData
from modules.usuarios.domain.schemas.registro_schemas import RegistroData
from modules.usuarios.domain.services.orchestrators.auth_orchestrator import (
    AuthOrchestrator,
)
from modules.usuarios.presentation.presenters.auth_presenter import AuthPresenter
from modules.usuarios.presentation.schemas.auth_schemas import (
    LoginDniIn,
    LoginEmailIn,
    LoginTokenOut,
    LoginUsernameIn,
    RegisterIn,
    SesionUsuarioOut,
)


@api_controller("/auth", tags=["Autenticación"])
class AuthController:
    """Alta de la cuenta, inicio de sesión y sesión actual."""

    @inject
    def __init__(
        self,
        auth_orchestrator: AuthOrchestrator,
        auth_presenter: AuthPresenter,
    ):
        self.auth_orchestrator = auth_orchestrator
        self.auth_presenter = auth_presenter

    @route.post(
        "/register",
        response={201: ApiResponse[LoginTokenOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Registra una cuenta pública y abre su sesión.",
    )
    async def register(self, request, payload: RegisterIn):
        """Registra una cuenta con su identidad.

        Route: POST /api/auth/register
        Auth: pública.

        El alta es el ÚNICO camino de nacimiento de una cuenta: nadie la crea
        como efecto lateral de consultar un documento (`FR-03` §1.2).

        La respuesta es el MISMO wrapper del inicio de sesión: el alta abre
        la sesión del actor recién creado, con su grupo funcional `Normal`.
        """
        data = RegistroData(
            persona=PersonaCreateData(
                tipo_documento=payload.tipoDocumento,
                numero_documento=payload.numeroDocumento,
                nombres=payload.nombres,
                apellidos=payload.apellidos,
                genero=payload.genero,
                telefono=payload.telefono or "",
                whatsapp=payload.whatsapp or "",
                contacto_emergencia_nombre=payload.contactoEmergenciaNombre or "",
                contacto_emergencia_telefono=payload.contactoEmergenciaTelefono or "",
            ),
            email=payload.email,
            password=payload.password,
        )
        result = await self.auth_orchestrator.registrar(data)
        return success_response(
            self.auth_presenter.present_login(result),
            message="El registro se completó correctamente.",
        )

    @route.post(
        "/login/username",
        response={200: ApiResponse[LoginTokenOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Inicia sesión con nombre de usuario y contraseña.",
    )
    async def login_username(self, request, payload: LoginUsernameIn):
        """Inicia sesión con el nombre de usuario.

        Route: POST /api/auth/login/username
        Auth: pública.

        Un identificador inexistente y una contraseña incorrecta producen la
        MISMA respuesta: el backend no publica qué cuentas existen.
        """
        result = await self.auth_orchestrator.login_username(
            payload.username,
            payload.password,
        )
        return success_response(
            self.auth_presenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )

    @route.post(
        "/login/dni",
        response={200: ApiResponse[LoginTokenOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Inicia sesión con documento de identidad y contraseña.",
    )
    async def login_dni(self, request, payload: LoginDniIn):
        """Inicia sesión con el documento de identidad.

        Route: POST /api/auth/login/dni
        Auth: pública.

        El documento RESUELVE la cuenta (atraviesa `Persona.numero_documento`);
        la credencial sigue siendo la contraseña. El documento no es una
        credencial: conocerlo no da acceso a la cuenta de otra persona.
        """
        result = await self.auth_orchestrator.login_dni(
            payload.dni,
            payload.password,
        )
        return success_response(
            self.auth_presenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )

    @route.post(
        "/login/email",
        response={200: ApiResponse[LoginTokenOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Inicia sesión con correo electrónico y contraseña.",
    )
    async def login_email(self, request, payload: LoginEmailIn):
        """Inicia sesión con el correo electrónico.

        Route: POST /api/auth/login/email
        Auth: pública.

        El email es la clave única y no nula de la cuenta: si no existe o no
        es único, no hay sesión.
        """
        result = await self.auth_orchestrator.login_email(
            payload.email,
            payload.password,
        )
        return success_response(
            self.auth_presenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )

    @route.get(
        "/me",
        response={200: ApiResponse[SesionUsuarioOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Devuelve los hechos de sesión del actor autenticado.",
    )
    async def me(self, request):
        """Devuelve los hechos de sesión del actor autenticado.

        Route: GET /api/auth/me
        Auth: requiere sesión.

        Lo que viaja son hechos DECIDIDOS POR EL BACKEND: el rol funcional
        (`Normal` / `Administrador`) y la política técnica de
        `core/capacidades.py`. El cliente los pinta; no los decide, y el
        backend vuelve a evaluarlos en cada petición.
        """
        result = await self.auth_orchestrator.sesion_actual(request.auth)
        return success_response(
            self.auth_presenter.present_sesion(result),
        )


__all__ = ["AuthController"]
