"""
RegistroPresenter — transforma RegistroTokenResult a esquema HTTP RegisterOut.
"""
from modules.usuarios.presentation.schemas.registro_schemas import RegisterOut, RegistroUserOut


class RegistroPresenter:
    """
    Transforma objetos de resultado del dominio a esquemas de respuesta HTTP.
    Desacopla el formateo de respuesta de los controladores.
    """

    @staticmethod
    def present_registro(result) -> RegisterOut:
        """
        Transforma un RegistroTokenResult a RegisterOut.

        Args:
            result: RegistroTokenResult del servicio de dominio

        Returns:
            Esquema RegisterOut listo para respuesta HTTP
        """
        return RegisterOut(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            expires_at=result.expires_at,
            user=RegistroUserOut(
                id=result.user.id,
                username=result.user.username,
                email=result.user.email,
                is_staff=result.user.is_staff,
                is_superuser=result.user.is_superuser,
                persona_id=result.user.persona_id,
            ),
        )