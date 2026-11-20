"""
`AuthCoreService` — operaciones de lectura y verificación de credenciales.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `FR-01` §4.4.

Es SYNC y NO abre `transaction.atomic()`: el llamador (el flujo) provee la
transacción si la hubiera (`contract/django-app-architecture-contract.md`
§4.3). Todo el acceso al ORM vive aquí.

Invariantes que implementa:

1. **El identificador civil NO es una credencial.** El login por DNI resuelve
   la cuenta atravesando la relación OPCIONAL `Usuario.persona_fk` y
   comparando `Persona.numero_documento` (`FR-03` §1.1). NO existe
   `Usuario.dni`, ni `dni_legacy`, ni ninguna columna de compatibilidad: el
   modelo de usuario del objetivo no se toca.
2. **El email es la clave ÚNICA y NO NULA de la cuenta** cuando existe
   (`unique_email_usuario_no_vacio`). Una cuenta sin email no puede iniciar
   sesión por email, y un email que resuelve a MÁS de una cuenta no autentica
   a ninguna: la unicidad es la que autoriza, no la última escritura.
3. **La contraseña se verifica por la autenticación de Django**
   (`django.contrib.auth.authenticate`). El servicio no reimplementa el
   hashing ni decide quién es una cuenta válida.
4. **Una cuenta inactiva es un estado DISTINTO de "credenciales inválidas"**:
   la contraseña es correcta, pero la cuenta no puede operar.
"""

import logging

from django.contrib.auth import authenticate
from django.utils import timezone
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import RefreshToken

from core.capacidades import (
    capacidades_de,
    es_admin,
    es_staff,
    es_superusuario,
    nivel_de,
)
from modules.usuarios.domain.models import Usuario
from modules.usuarios.domain.results import SesionUsuarioResult
from modules.usuarios.domain.schemas import normalizar_numero_documento
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService

logger = logging.getLogger(__name__)

#: Veredictos de la verificación de credenciales.
#:
#: Son un vocabulario CERRADO: el flujo los traduce a las excepciones de
#: dominio y nunca construye prosa pública por su cuenta.
VERDICTO_AUTENTICADO = "AUTENTICADO"
VERDICTO_CREDENCIALES_INVALIDAS = "CREDENCIALES_INVALIDAS"
VERDICTO_CUENTA_INACTIVA = "CUENTA_INACTIVA"


class AuthCoreService:
    """Resolución de cuentas y verificación de credenciales."""

    def __init__(self, grupo_service: GrupoFuncionalService | None = None):
        self.grupo_service = grupo_service or GrupoFuncionalService()

    # ── Resolución de la cuenta por identificador ──────────────────────────

    def buscar_por_username(self, username: str):
        """La cuenta con ese `username`, o `None`."""
        candidato = str(username or "").strip()
        if not candidato:
            return None
        return Usuario.objects.filter(username=candidato).order_by("created_at").first()

    def buscar_por_email(self, email: str):
        """La cuenta con ese email, o `None`.

        El email es la clave ÚNICA y NO NULA de la cuenta
        (`unique_email_usuario_no_vacio`). La comparación NO distingue
        mayúsculas porque el usuario lo escribe como lo escribe; si el
        resultado fuera AMBIGUO (más de una cuenta), NO se autentica a
        ninguna: la unicidad es lo que autoriza.
        """
        correo = str(email or "").strip()
        if not correo:
            return None
        candidatos = list(
            Usuario.objects.all()
            .filter(email__iexact=correo)
            .exclude(email__isnull=True)
            .exclude(email="")
            .order_by("created_at")[:2]
        )
        if len(candidatos) != 1:
            if len(candidatos) > 1:
                logger.warning("Email ambiguo en el inicio de sesión.")
            return None
        return candidatos[0]

    def buscar_por_documento(self, numero_documento: str):
        """La cuenta vinculada a la `Persona` con ese documento, o `None`.

        Atraviesa la relación OPCIONAL `Usuario.persona_fk`: una cuenta técnica
        (sin `Persona`) NO puede entrar por documento, y una `Persona` sin
        cuenta tampoco resuelve a ninguna cuenta (`FR-03` §1.1, §1.2).

        El documento se NORMALIZA antes de comparar
        (`normalizar_numero_documento`): el valor persistido siempre lo está,
        así que la comparación es exacta y sin ambigüedad de formato.

        Si el número resuelve a MÁS de una cuenta, NO se autentica a ninguna:
        un identificador que no es único no puede ser una credencial.
        """
        numero = normalizar_numero_documento(numero_documento)
        if not numero:
            return None
        candidatos = list(
            Usuario.objects.all()
            .filter(persona_fk__numero_documento=numero)
            .order_by("created_at")[:2]
        )
        if len(candidatos) != 1:
            if len(candidatos) > 1:
                logger.warning("Documento ambiguo en el inicio de sesión.")
            return None
        return candidatos[0]

    # ── Verificación de credenciales ───────────────────────────────────────

    def verificar_credenciales(self, usuario, password: str) -> str:
        """Veredicto de la pareja (cuenta, contraseña).

        La contraseña se verifica por la autenticación de Django. Django
        devuelve `None` tanto para una contraseña incorrecta como para una
        cuenta inactiva, así que el caso inactivo se discrimina con la
        verificación del hash: sólo una cuenta DESACTIVADA con la contraseña
        CORRECTA pasa de "credenciales inválidas" a "cuenta inactiva".
        """
        if usuario is None:
            return VERDICTO_CREDENCIALES_INVALIDAS

        autenticado = authenticate(username=usuario.username, password=password)
        if autenticado is not None:
            return VERDICTO_AUTENTICADO

        if not usuario.is_active and usuario.check_password(password):
            return VERDICTO_CUENTA_INACTIVA

        return VERDICTO_CREDENCIALES_INVALIDAS

    # ── Emisión de tokens ──────────────────────────────────────────────────

    def crear_tokens(self, usuario) -> tuple[str, str, object]:
        """Emite el par de tokens JWT y el instante de expiración del acceso.

        `django-ninja-jwt` es el ÚNICO emisor: el refresco y la verificación
        los sirve el `NinjaJWTDefaultController` ya registrado y este paquete
        NO duplica esa lógica.
        """
        refresh = RefreshToken.for_user(usuario)
        expira_en = timezone.now() + api_settings.ACCESS_TOKEN_LIFETIME
        return str(refresh.access_token), str(refresh), expira_en

    # ── Hechos de sesión ───────────────────────────────────────────────────

    def construir_sesion(self, usuario) -> SesionUsuarioResult:
        """Construye los hechos de sesión que publica el backend.

        Son todos autos (del propio llamador) y los calcula el BACKEND: el
        grupo funcional de negocio (`FR-03` §1.2) y la política técnica de
        `core/capacidades.py` (el único mapa del proyecto). El cliente los
        pinta; no los decide (`contratos/02` §3).
        """
        persona = usuario.persona_fk
        return SesionUsuarioResult(
            id=str(usuario.id),
            username=usuario.username,
            email=usuario.email or None,
            nombres=persona.nombres if persona else None,
            apellidos=(persona.apellidos or None) if persona else None,
            persona_id=str(persona.id) if persona else None,
            rol=self.grupo_service.nivel_rol(usuario),
            grupos=sorted(self.grupo_service.grupos_de(usuario)),
            es_admin=es_admin(usuario),
            is_staff=es_staff(usuario),
            is_superuser=es_superusuario(usuario),
            nivel=nivel_de(usuario),
            capacidades=sorted(capacidades_de(usuario)),
        )


__all__ = [
    "VERDICTO_AUTENTICADO",
    "VERDICTO_CREDENCIALES_INVALIDAS",
    "VERDICTO_CUENTA_INACTIVA",
    "AuthCoreService",
]
