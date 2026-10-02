"""
AuthPresenter — transforma LoginTokenResult a esquema HTTP LoginTokenOut.
"""
from modules.usuarios.presentation.schemas.auth_schemas import LoginTokenOut, AuthUserOut


class AuthPresenter:
    """
    Transforma objetos de resultado del dominio a esquemas de respuesta HTTP.
    Desacopla el formateo de respuesta de los controladores.
    """

    @staticmethod
    def present_login(result) -> LoginTokenOut:
        """
        Transforma un LoginTokenResult a LoginTokenOut.

        Args:
            result: LoginTokenResult del servicio de dominio

        Returns:
            Esquema LoginTokenOut listo para respuesta HTTP
        """
        return LoginTokenOut(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            expires_at=result.expires_at,
            user=AuthUserOut(
                id=result.user.id,
                username=result.user.username,
                email=result.user.email,
                is_staff=result.user.is_staff,
                is_superuser=result.user.is_superuser,
                persona_id=result.user.persona_id,
                dni_legacy=result.user.dni_legacy,
            ),
        )
