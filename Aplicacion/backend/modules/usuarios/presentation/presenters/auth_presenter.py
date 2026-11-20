"""
Presenters de autenticación y sesión.

Freeze: `FREEZE-PS-1.0.0` (`FR-07` §4).

Reglas (`contract/PLAN_REFACTORIZACION.md` §3.A,
`contract/api-wrapper-presenter-contract.md` §3):

- El presenter TRANSFORMA un resultado de dominio en un schema HTTP.
- No consulta la base de datos, no llama a selectores y no elige mensajes.
- Sólo tiene métodos `@staticmethod` / `@classmethod`.
"""

from modules.usuarios.domain.results import LoginTokenResult, SesionUsuarioResult
from modules.usuarios.presentation.schemas.auth_schemas import (
    LoginTokenOut,
    SesionUsuarioOut,
)


class AuthPresenter:
    """Presenter de la autenticación y de la sesión."""

    @staticmethod
    def present_login(result: LoginTokenResult) -> LoginTokenOut:
        """Traduce el resultado del login al wrapper HTTP."""
        return LoginTokenOut(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            expires_at=result.expires_at,
            user=AuthPresenter.present_sesion(result.user),
        )

    @staticmethod
    def present_sesion(result: SesionUsuarioResult) -> SesionUsuarioOut:
        """Traduce los hechos de sesión al wrapper HTTP.

        Es el MISMO wrapper que devuelve `/auth/me`: el login y la sesión
        publica exactamente la misma forma, así que el cliente espeja un
        solo tipo.
        """
        return SesionUsuarioOut(
            id=result.id,
            persona_id=result.persona_id,
            username=result.username,
            email=result.email,
            nombres=result.nombres,
            apellidos=result.apellidos,
            rol=result.rol,
            grupos=list(result.grupos),
            es_admin=result.es_admin,
            is_staff=result.is_staff,
            is_superuser=result.is_superuser,
            nivel=result.nivel,
            capacidades=list(result.capacidades),
        )


__all__ = ["AuthPresenter"]
