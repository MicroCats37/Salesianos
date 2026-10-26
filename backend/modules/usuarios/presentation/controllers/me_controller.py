"""
MeController — endpoint GET /auth/me que devuelve el usuario autenticado.

Permite que el front revalide el token tras recargar la página.
"""
from typing import Optional

from ninja import Schema
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.responses import ApiResponse, success_response


class MeOut(Schema):
    id: str
    username: str
    email: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    rol: Optional[str] = None
    es_admin: bool = False
    persona_id: Optional[str] = None


@api_controller("/auth", tags=["Autenticación"])
class AuthMeController:
    """
    Devuelve los datos del usuario autenticado a partir del JWT.
    Usado por el shell de hidratación del front para revalidar el token
    después de un reload.

    Rutas:
      GET /auth/me -> me
    """

    @route.get(
        "/me",
        response={200: ApiResponse[MeOut]},
        auth=JWTAuth(),
    )
    def me(self, request):
        """
        Devuelve los datos del usuario autenticado.

        Route: GET /api/auth/me
        Auth: JWT required.
        Returns: id, username, email, nombres, apellidos, rol, es_admin,
                 persona_id del usuario.
                 Si no está autenticado, retorna data=None (no lanza error).

        `es_admin` es la ÚNICA bandera de autorización que consume el cliente y
        se calcula en el servidor con la regla del proyecto:

            admin = is_staff OR is_superuser

        Es la misma regla que aplica `core.permissions.RequireAdmin`, así que el
        frontend puede anticipar un 403 sin ser la autoridad: la sesión del
        cliente no decide nada, el backend vuelve a evaluarla en cada petición.

        `is_superuser` NUNCA se expone: el nivel de break-glass no es
        asignable ni visible desde la UI de administración.
        """
        usuario = request.user
        if usuario is None or not usuario.is_authenticated:
            return success_response(None)

        persona = getattr(usuario, "persona_fk", None)
        nombres = getattr(persona, "nombres", None) if persona else None
        apellidos = getattr(persona, "apellidos", None) if persona else None

        es_admin = bool(
            getattr(usuario, "is_staff", False)
            or getattr(usuario, "is_superuser", False)
        )
        # `rol` se mantiene por compatibilidad con clientes existentes, pero se
        # deriva de la MISMA regla que `es_admin` para que el vocabulario no
        # pueda divergir (antes un usuario staff recibía "staff" y no "admin",
        # pese a ser administrador para efectos de autorización).
        rol = "admin" if es_admin else "user"

        return success_response(
            {
                "id": str(usuario.id),
                "username": getattr(usuario, "username", "") or "",
                "email": getattr(usuario, "email", None),
                "nombres": nombres,
                "apellidos": apellidos,
                "rol": rol,
                "es_admin": es_admin,
                "persona_id": str(persona.id) if persona else None,
            }
        )
