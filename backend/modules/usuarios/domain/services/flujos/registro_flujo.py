"""
RegistroFlujo — flujo de negocio asíncrono para registro de usuarios.

Usa sync_to_async para envolver operaciones ORM de servicios core.
Maneja transaction.atomic para crear Persona + Usuario de forma atómica.
"""
from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from ninja.errors import HttpError

from injector import inject
from modules.usuarios.domain.models import Persona, Usuario
from modules.usuarios.domain.services.core.auth_core_service import AuthCoreService
from modules.usuarios.domain.services.core.persona_core_service import PersonaCoreService
from modules.usuarios.domain.schemas.registro_result_schemas import RegistroTokenResult, RegistroUserResult


class RegistroFlujo:
    """
    Flujo asíncrono para registro de usuario con Persona.

    Pasos:
    1. Validar que no exista usuario con el mismo email.
    2. Buscar si existe Persona con (tipo_documento, numero_documento).
    3. Si no existe Persona: crear Persona + Usuario + acepto_bases=True.
    4. Si existe Persona sin usuario: crear Usuario + acepto_bases=True, vincular.
    5. Si existe Persona con usuario: error 409 conflict.
    """

    @inject
    def __init__(
        self,
        persona_core: PersonaCoreService,
        auth_core: AuthCoreService,
    ):
        self.persona_core = persona_core
        self.auth_core = auth_core

    def _generar_username(self, tipo_documento: str, numero_documento: str) -> str:
        """Genera username único: dni_12345678."""
        return f"{tipo_documento.lower()}_{numero_documento}"

    async def _proceso_registro(
        self,
        email: str,
        password: str,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellidos: str,
        genero: str,
        aceptacion_ip: str | None,
        aceptacion_user_agent: str | None,
        telefono: str | None = None,
        whatsapp: str | None = None,
        contacto_emergencia_nombre: str | None = None,
        contacto_emergencia_telefono: str | None = None,
    ) -> RegistroTokenResult:
        """
        Flujo completo de registro.

        Returns RegistroTokenResult con tokens JWT y datos del usuario.
        Raises HttpError 409 si el documento ya tiene usuario asociado.
        Raises HttpError 409 si el email ya está registrado.
        """
        # Paso 1: Buscar si existe Persona con ese documento
        persona = await sync_to_async(self.persona_core._get_persona_por_documento)(
            tipo_documento, numero_documento
        )

        if persona is None:
            # Paso 2a: Crear Persona nueva + Usuario + acepto_bases=True
            result = await self._crear_persona_y_usuario(
                email=email,
                password=password,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                nombres=nombres,
                apellidos=apellidos,
                genero=genero,
                telefono=telefono,
                whatsapp=whatsapp,
                contacto_emergencia_nombre=contacto_emergencia_nombre,
                contacto_emergencia_telefono=contacto_emergencia_telefono,
            )
        else:
            # Paso 2b: Persona existe — verificar si tiene usuario asociado
            usuario_existente = await sync_to_async(
                lambda: Usuario.objects.filter(persona_fk=persona).first()
            )()
            if usuario_existente is not None:
                raise HttpError(409, "Ya existe una cuenta con este documento")
            # Crear Usuario vinculado a Persona existente
            result = await self._crear_usuario_vinculado(
                persona=persona,
                email=email,
                password=password,
            )

        return result

    async def _crear_persona_y_usuario(
        self,
        email: str,
        password: str,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellidos: str,
        genero: str,
        telefono: str | None = None,
        whatsapp: str | None = None,
        contacto_emergencia_nombre: str | None = None,
        contacto_emergencia_telefono: str | None = None,
    ) -> RegistroTokenResult:
        """Crea Persona nueva + Usuario + acepto_bases=True dentro de transaction.atomic."""

        @sync_to_async
        def _atomic_creacion():
            with transaction.atomic():
                # Crear Persona
                persona_data = {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "tipo_documento": tipo_documento,
                    "numero_documento": numero_documento,
                    "genero": genero,
                    "acepto_bases": True,
                }
                if telefono:
                    persona_data["telefono"] = telefono
                if whatsapp:
                    persona_data["whatsapp"] = whatsapp
                if contacto_emergencia_nombre:
                    persona_data["contacto_emergencia_nombre"] = contacto_emergencia_nombre
                if contacto_emergencia_telefono:
                    persona_data["contacto_emergencia_telefono"] = contacto_emergencia_telefono

                persona = Persona.objects.create(**persona_data)

                # Crear Usuario vinculado
                username = self._generar_username(tipo_documento, numero_documento)
                usuario = Usuario(
                    username=username,
                    email=email,
                    persona_fk=persona,
                )
                usuario.set_password(password)
                usuario.save()

                # Crear tokens (sync version — we're inside a sync context via sync_to_async)
                access_token, refresh_token, expires_at = self.auth_core._create_jwt_tokens(usuario)

                # Construir resultado
                user_result = RegistroUserResult(
                    id=usuario.id,
                    username=usuario.username,
                    email=usuario.email,
                    is_staff=usuario.is_staff,
                    is_superuser=usuario.is_superuser,
                    persona_id=persona.id,
                )
                return RegistroTokenResult(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    user=user_result,
                )

        try:
            result = await _atomic_creacion()
        except IntegrityError as e:
            if "email" in str(e).lower() or "duplicate" in str(e).lower():
                raise HttpError(409, "El email ya está registrado")
            raise HttpError(409, "Error de integridad de datos")

        return result

    async def _crear_usuario_vinculado(
        self,
        persona: Persona,
        email: str,
        password: str,
    ) -> RegistroTokenResult:
        """Crea Usuario vinculado a Persona existente + acepto_bases=True dentro de transaction.atomic."""

        @sync_to_async
        def _atomic_vinculacion():
            with transaction.atomic():
                # Set acepto_bases=True on existing Persona
                persona.acepto_bases = True
                persona.save(update_fields=["acepto_bases"])

                username = self._generar_username(persona.tipo_documento, persona.numero_documento)
                usuario = Usuario(
                    username=username,
                    email=email,
                    persona_fk=persona,
                )
                usuario.set_password(password)
                usuario.save()

                # Crear tokens (sync version — we're inside a sync context via sync_to_async)
                access_token, refresh_token, expires_at = self.auth_core._create_jwt_tokens(usuario)

                # Construir resultado
                user_result = RegistroUserResult(
                    id=usuario.id,
                    username=usuario.username,
                    email=usuario.email,
                    is_staff=usuario.is_staff,
                    is_superuser=usuario.is_superuser,
                    persona_id=persona.id,
                )
                return RegistroTokenResult(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    user=user_result,
                )

        try:
            result = await _atomic_vinculacion()
        except IntegrityError as e:
            if "email" in str(e).lower() or "duplicate" in str(e).lower():
                raise HttpError(409, "El email ya está registrado")
            raise HttpError(409, "Error de integridad de datos")

        return result
