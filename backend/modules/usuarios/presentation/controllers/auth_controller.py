"""
AuthController — controladores HTTP ligeros para endpoints de login.

Solo delega a AuthOrchestrator y retorna vía presenter.
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject

from core.responses import ApiResponse, success_response
from modules.usuarios.presentation.schemas.auth_schemas import (
    LoginUsernameIn,
    LoginDniIn,
    LoginEmailIn,
    LoginTokenOut,
)
from modules.usuarios.presentation.presenters.auth_presenter import AuthPresenter
from modules.usuarios.domain.services.orchestrators.auth_orchestrator import AuthOrchestrator


@api_controller("/auth/login", tags=["Autenticación"], permissions=[AllowAny])
class AuthLoginController:
    """
    Controlador para login JWT modular por username, DNI o email.

    Cada endpoint:
    1. Recibe el payload
    2. Delega a AuthOrchestrator
    3. Transforma el resultado vía AuthPresenter
    4. Retorna la respuesta HTTP

    Rutas:
      POST /auth/login/username -> login_username
      POST /auth/login/dni      -> login_dni
      POST /auth/login/email    -> login_email
    """

    @inject
    def __init__(self, auth_orchestrator: AuthOrchestrator):
        self.auth_orchestrator = auth_orchestrator

    @route.post("/username", response={200: ApiResponse[LoginTokenOut]}, auth=None)
    async def login_username(self, payload: LoginUsernameIn):
        """
        Login con username + password.

        Route: POST /api/auth/login/username
        Auth: public (no JWT).
        Returns: JWT access_token + refresh_token + expires_at + datos del usuario.
        Errors: ValueError con código AUTH_ERROR si credenciales inválidas (401).
        """
        result = await self.auth_orchestrator.login_username(
            username=payload.username,
            password=payload.password,
        )
        return success_response(
            AuthPresenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )

    @route.post("/dni", response={200: ApiResponse[LoginTokenOut]}, auth=None)
    async def login_dni(self, payload: LoginDniIn):
        """
        Login con DNI + password.

        Route: POST /api/auth/login/dni
        Auth: public (no JWT).
        Returns: JWT access_token + refresh_token + expires_at + datos del usuario.
        Errors: ValueError con código AUTH_ERROR si credenciales inválidas (401).
        """
        result = await self.auth_orchestrator.login_dni(
            dni=payload.dni,
            password=payload.password,
        )
        return success_response(
            AuthPresenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )

    @route.post("/email", response={200: ApiResponse[LoginTokenOut]}, auth=None)
    async def login_email(self, payload: LoginEmailIn):
        """
        Login con email + password.

        Route: POST /api/auth/login/email
        Auth: public (no JWT).
        Returns: JWT access_token + refresh_token + expires_at + datos del usuario.
        Errors: ValueError con código AUTH_ERROR si credenciales inválidas (401).
        """
        result = await self.auth_orchestrator.login_email(
            email=payload.email,
            password=payload.password,
        )
        return success_response(
            AuthPresenter.present_login(result),
            message="Inicio de sesión exitoso.",
        )
