"""
`RegistroFlujo` — el alta de una cuenta con su identidad.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.1, §1.2 y §3.2 regla 3.

Es async y ABRE `transaction.atomic()`: la cuenta y su identidad nacen
juntas o no nacen (`contract/django-app-architecture-contract.md` §4.4).

Las reglas congeladas que implementa este flujo:

1. **El nacimiento de una cuenta es una operación EXPLICITA.** Nadie crea una
   cuenta como efecto lateral de consultar un documento, de asignar un pase o
   de prellenar datos (`FR-03` §1.2). Este flujo es el único camino.
2. **La identidad no se reescribe.** Si la `Persona` del documento YA existe
   pero NO tiene cuenta, la cuenta se le ADJUNTA: sus datos son los de la
   fuente de verdad y este flujo no los pisa. Si ya tiene cuenta, el
   documento está en uso y el alta se rechaza con `PERSONA_DUPLICADA`
   (`FR-03` §1.1).
3. **El email es la clave ÚNICA y NO NULA de la cuenta**
   (`unique_email_usuario_no_vacio`). Un email ya usado se rechaza con un
   conflicto 409.
4. **La carrera la resuelve la base de datos.** La unicidad la garantizan las
   `UniqueConstraint`; este flujo NO usa `get_or_create` silencioso, que
   ocultaría la carrera: captura el `IntegrityError` y decide el conflicto por
   el estado real (`FR-03` §3.2 regla 3).
5. **La cuenta nace en el grupo `Normal`.** Los dos grupos funcionales son
   `Normal` y `Administrador` (`FR-03` §1.2); una cuenta recién creada no
   administra nada.
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.usuarios.domain.constants import GrupoFuncionalChoices
from modules.usuarios.domain.exceptions import (
    EmailYaRegistradoError,
    PersonaDuplicadaError,
)
from modules.usuarios.domain.results import LoginTokenResult
from modules.usuarios.domain.schemas.registro_schemas import RegistroData
from modules.usuarios.domain.selectors import UsuarioSelector
from modules.usuarios.domain.services.core.auth_core_service import AuthCoreService
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService
from modules.usuarios.domain.services.core.persona_core_service import (
    PersonaCoreService,
)
from modules.usuarios.domain.services.core.registro_core_service import (
    RegistroCoreService,
)


class RegistroFlujo:
    """El caso de uso async del alta de una cuenta."""

    @inject
    def __init__(
        self,
        registro_core: RegistroCoreService,
        persona_core: PersonaCoreService,
        usuario_selector: UsuarioSelector,
        auth_core: AuthCoreService,
        grupo_service: GrupoFuncionalService,
    ):
        self.registro_core = registro_core
        self.persona_core = persona_core
        self.usuario_selector = usuario_selector
        self.auth_core = auth_core
        self.grupo_service = grupo_service

    # ── El caso de uso ──────────────────────────────────────────────────────

    async def _proceso_registro(self, data: RegistroData) -> LoginTokenResult:
        """Registra la cuenta y abre la sesión del actor."""
        persona = await sync_to_async(self._persona_del_documento)(data)

        if persona is not None:
            await self._verificar_sin_cuenta(persona)

        usuario = await sync_to_async(self._crear_cuenta_atomica)(data, persona)

        await sync_to_async(self.grupo_service.asignar_grupo)(
            usuario,
            GrupoFuncionalChoices.NORMAL.value,
        )

        access_token, refresh_token, expira_en = await sync_to_async(
            self.auth_core.crear_tokens
        )(usuario)
        sesion = await sync_to_async(self.auth_core.construir_sesion)(usuario)

        return LoginTokenResult(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expira_en,
            user=sesion,
        )

    # ── Interno ────────────────────────────────────────────────────────────

    def _persona_del_documento(self, data: RegistroData):
        """La `Persona` del documento, o `None` si todavía no existe."""
        return self.persona_core.obtener_por_documento(
            data.persona.tipo_documento,
            data.persona.numero_documento,
        )

    async def _verificar_sin_cuenta(self, persona) -> None:
        """Rechaza el alta si ese documento ya tiene una cuenta."""
        cuenta = await sync_to_async(self.usuario_selector.obtener_por_persona)(
            persona.id
        )
        if cuenta is not None:
            raise PersonaDuplicadaError()

    def _crear_cuenta_atomica(self, data: RegistroData, persona_existente):
        """Crea la identidad (si falta) y la cuenta, en UNA transacción."""
        try:
            with transaction.atomic():
                if self.registro_core.email_en_uso(data.email):
                    raise EmailYaRegistradoError()

                persona = persona_existente or self.persona_core.crear(data.persona)

                username = self.registro_core.username_para(
                    persona.tipo_documento,
                    persona.numero_documento,
                )
                return self.registro_core.crear_cuenta(
                    username=username,
                    email=data.email,
                    password=data.password,
                    persona_fk=persona,
                )
        except IntegrityError:
            # La carrera la resuelve la base de datos. Se decide el conflicto
            # por el estado REAL, no por el texto de la excepción.
            if self.registro_core.email_en_uso(data.email):
                raise EmailYaRegistradoError() from None
            raise PersonaDuplicadaError() from None


__all__ = ["RegistroFlujo"]
