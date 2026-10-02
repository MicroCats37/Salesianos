"""
RegistroController — controlador HTTP ligero para endpoint de registro.

Solo delega a RegistroOrchestrator y retorna vía presenter.
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject

from core.responses import ApiResponse, success_response
from modules.usuarios.presentation.schemas.registro_schemas import RegisterIn, RegisterOut
from modules.usuarios.presentation.presenters.registro_presenter import RegistroPresenter
from modules.usuarios.domain.services.orchestrators.registro_orchestrator import RegistroOrchestrator


@api_controller("/auth", tags=["Autenticación"], permissions=[AllowAny])
class RegistroController:
    """
    Controlador para registro de usuarios responsables.

    Cada endpoint:
    1. Recibe el payload
    2. Delega a RegistroOrchestrator
    3. Transforma el resultado vía RegistroPresenter
    4. Retorna la respuesta HTTP

    Rutas:
      POST /auth/register -> register
    """

    @inject
    def __init__(self, registro_orchestrator: RegistroOrchestrator):
        self.registro_orchestrator = registro_orchestrator

    @route.post("/register", response={200: ApiResponse[RegisterOut]}, auth=None)
    async def register(self, request, payload: RegisterIn):
        """
        Registro de usuario responsable con datos de Persona.

        Route: POST /api/auth/register
        Auth: public (no JWT).
        Side effects: crea una Persona (si no existe para ese documento) + Usuario + Aceptación BASES.
        Returns: JWT access_token + refresh_token + expires_at + datos del usuario.
        Errors: BusinessError/IntegrityError si email o documento ya registrados (409).
        """
        result = await self.registro_orchestrator.registrar(
            email=payload.email,
            password=payload.password,
            tipo_documento=payload.tipoDocumento,
            numero_documento=payload.numeroDocumento,
            nombres=payload.nombres,
            apellidos=payload.apellidos,
            genero=payload.genero,
            aceptacion_ip=self._get_client_ip(request),
            aceptacion_user_agent=request.META.get("HTTP_USER_AGENT", ""),
            telefono=payload.telefono,
            whatsapp=payload.whatsapp,
            contacto_emergencia_nombre=payload.contactoEmergenciaNombre,
            contacto_emergencia_telefono=payload.contactoEmergenciaTelefono,
        )
        return success_response(
            RegistroPresenter.present_registro(result),
            message="Registro exitoso. Ya puedes iniciar sesión.",
        )

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """Obtiene la IP del cliente desde el request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")