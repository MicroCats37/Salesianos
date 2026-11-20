"""
`AuthOrchestrator` — fachada async de la autenticación.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `FR-07` (rutas de sesión).

Es DELGADA: un método por endpoint, y sólo delega en el flujo
(`contract/django-app-architecture-contract.md` §4.5,
`contract/PLAN_REFACTORIZACION.md` §1.A).

Los fallos NO se construyen aquí: el flujo los lanza como excepciones de
dominio con código estable y el catálogo público de `core/exceptions.py` los
convierte en la respuesta HTTP (`contract/api-wrapper-presenter-contract.md`
§8). El controller nunca construye respuestas de error.
"""

from injector import inject

from modules.usuarios.domain.results import LoginTokenResult, SesionUsuarioResult
from modules.usuarios.domain.services.flujos.auth_flujo import AuthFlujo


class AuthOrchestrator:
    """Fachada async de las operaciones de autenticación y sesión."""

    @inject
    def __init__(self, flujo: AuthFlujo):
        self.flujo = flujo

    # ── Inicio de sesión ───────────────────────────────────────────────────

    async def login_username(self, username: str, password: str) -> LoginTokenResult:
        """Inicio de sesión por nombre de usuario."""
        return await self.flujo._proceso_login_username(username, password)

    async def login_dni(self, dni: str, password: str) -> LoginTokenResult:
        """Inicio de sesión por documento de identidad."""
        return await self.flujo._proceso_login_dni(dni, password)

    async def login_email(self, email: str, password: str) -> LoginTokenResult:
        """Inicio de sesión por email."""
        return await self.flujo._proceso_login_email(email, password)

    # ── Sesión actual ──────────────────────────────────────────────────────

    async def sesion_actual(self, usuario) -> SesionUsuarioResult:
        """Hechos de sesión del actor autenticado."""
        return await self.flujo._proceso_sesion_actual(usuario)


__all__ = ["AuthOrchestrator"]
