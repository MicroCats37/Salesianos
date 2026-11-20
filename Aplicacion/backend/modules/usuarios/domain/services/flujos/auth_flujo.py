"""
`AuthFlujo` — inicio de sesión y sesión actual.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `FR-01` §4.4.

Es async y NO abre `transaction.atomic()`: el inicio de sesión sólo LEE y
emite tokens, no escribe estado de negocio
(`contract/django-app-architecture-contract.md` §4.4,
`contract/PLAN_REFACTORIZACION.md` §4).

Reglas congeladas que implementa este flujo:

1. **Una sola forma de fallo para el cliente.** Un identificador inexistente
   y una contraseña incorrecta producen EXACTAMENTE la misma respuesta: mismo
   status, mismo código (`AUTH_ERROR`) y misma prosa pública. El backend no
   publica qué cuentas existen (`RN-U04`).
2. **El identificador civil no es una credencial.** El login por DNI resuelve
   la cuenta atravesando `Usuario.persona_fk` y comparando
   `Persona.numero_documento`. No hay `Usuario.dni` ni ningún campo de
   compatibilidad (`FR-03` §1.1).
3. **Una cuenta inactiva es un estado distinto.** La contraseña es correcta
   pero la cuenta no puede operar: responde 403 con código estable, no el
   mismo 401 de "credenciales inválidas" (`FR-01` §4.4).
4. **La sesión se abre con los tokens de `django-ninja-jwt`.** El refresco y
   la verificación los sirve el `NinjaJWTDefaultController` ya registrado;
   este paquete NO duplica esa lógica.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.usuarios.domain.exceptions import (
    CredencialesInvalidasError,
    CuentaInactivaError,
)
from modules.usuarios.domain.results import LoginTokenResult, SesionUsuarioResult
from modules.usuarios.domain.services.core.auth_core_service import (
    VERDICTO_AUTENTICADO,
    VERDICTO_CUENTA_INACTIVA,
    AuthCoreService,
)


class AuthFlujo:
    """Casos de uso de autenticación y de sesión."""

    @inject
    def __init__(self, auth_core_service: AuthCoreService):
        self.auth_core_service = auth_core_service

    # ── Inicio de sesión ───────────────────────────────────────────────────

    async def _proceso_login_username(
        self,
        username: str,
        password: str,
    ) -> LoginTokenResult:
        """Inicio de sesión por nombre de usuario."""
        usuario = await sync_to_async(
            self.auth_core_service.buscar_por_username
        )(username)
        return await self._abrir_sesion(usuario, password)

    async def _proceso_login_dni(
        self,
        dni: str,
        password: str,
    ) -> LoginTokenResult:
        """Inicio de sesión por documento de identidad.

        El documento se resuelve por `Persona.numero_documento`: es un
        IDENTIFICADOR, no una credencial (`FR-03` §1.1).
        """
        usuario = await sync_to_async(
            self.auth_core_service.buscar_por_documento
        )(dni)
        return await self._abrir_sesion(usuario, password)

    async def _proceso_login_email(
        self,
        email: str,
        password: str,
    ) -> LoginTokenResult:
        """Inicio de sesión por email (clave única y no nula de la cuenta)."""
        usuario = await sync_to_async(
            self.auth_core_service.buscar_por_email
        )(email)
        return await self._abrir_sesion(usuario, password)

    # ── Sesión actual ──────────────────────────────────────────────────────

    async def _proceso_sesion_actual(self, usuario) -> SesionUsuarioResult:
        """Hechos de sesión del actor autenticado.

        Es una proyección AUTOS del propio llamador: la autorización NO sale
        de aquí, la vuelve a evaluar el backend en cada petición
        (`contratos/02` §3, `RN-A01`).
        """
        return await sync_to_async(self.auth_core_service.construir_sesion)(usuario)

    # ── Interno ────────────────────────────────────────────────────────────

    async def _abrir_sesion(self, usuario, password: str) -> LoginTokenResult:
        """Verifica las credenciales y emite el par de tokens.

        El fallo es NEUTRO: una cuenta que no existe y una contraseña
        incorrecta se responden igual. Sólo la cuenta desactivada con la
        contraseña correcta se distingue, porque es otro estado de negocio.
        """
        if usuario is None:
            raise CredencialesInvalidasError()

        veredicto = await sync_to_async(
            self.auth_core_service.verificar_credenciales
        )(usuario, password)

        if veredicto == VERDICTO_CUENTA_INACTIVA:
            raise CuentaInactivaError()
        if veredicto != VERDICTO_AUTENTICADO:
            raise CredencialesInvalidasError()

        access_token, refresh_token, expira_en = await sync_to_async(
            self.auth_core_service.crear_tokens
        )(usuario)
        sesion = await sync_to_async(
            self.auth_core_service.construir_sesion
        )(usuario)

        return LoginTokenResult(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expira_en,
            user=sesion,
        )


__all__ = ["AuthFlujo"]
