"""
Esquemas HTTP de autenticación y sesión.

Todos heredan de `core.types.BaseSchema`
(`contract/PLAN_REFACTORIZACION.md` §1.C): los strings vacíos se
normalizan a `None` antes de validar.

La composición sigue los tres bloques de
`contract/SCHEMA_DRY_INTENTION.md`:

- `SesionIdentidadOut` — bloque IDENTIDAD (id de la cuenta y de su persona).
- `SesionCuentaOut` — bloque GENERAL (datos de la cuenta y de su persona).
- `SesionRolOut` — bloque ESPECÍFICO (los hechos de rol que publica el
  backend).
- `SesionUsuarioOut` — la composición de los tres: el ÚNICO wrapper de
  sesión, compartido por el login y por `/auth/me`.
- `LoginTokenOut` — el caso de uso del login: tokens + la sesión.

`LoginTokenOut` y `SesionUsuarioOut` NO exponen la contraseña, el hash, el
token de refresco en claro ni ningún campo de compatibilidad del backend
congelado: el modelo de usuario del objetivo no tiene `dni` ni `dni_legacy`.
"""

from datetime import datetime

from core.types import BaseSchema
from ninja import Field


class LoginUsernameIn(BaseSchema):
    """Entrada del inicio de sesión por nombre de usuario."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Nombre de usuario de la cuenta.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Contraseña de la cuenta.",
    )


class LoginDniIn(BaseSchema):
    """Entrada del inicio de sesión por documento de identidad.

    El documento es un IDENTIFICADOR, no una credencial: se usa para
    ENCONTRAR la cuenta y la contraseña sigue siendo la credencial
    (`FR-03` §1.1).
    """

    dni: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Documento de identidad de la persona vinculada a la cuenta.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Contraseña de la cuenta.",
    )


class LoginEmailIn(BaseSchema):
    """Entrada del inicio de sesión por email.

    El email es la clave ÚNICA y NO NULA de la cuenta
    (`unique_email_usuario_no_vacio`).
    """

    email: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Correo electrónico de la cuenta.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Contraseña de la cuenta.",
    )


class SesionIdentidadOut(BaseSchema):
    """Bloque IDENTIDAD: identificadores de la cuenta y de su persona."""

    id: str = Field(..., description="Identificador interno de la cuenta.")
    persona_id: str | None = Field(
        None,
        description="Identificador de la persona vinculada. Nulo si la cuenta "
        "no tiene persona (cuenta técnica).",
    )


class SesionCuentaOut(BaseSchema):
    """Bloque GENERAL: datos de la cuenta y de su persona."""

    username: str = Field(..., description="Nombre de usuario de la cuenta.")
    email: str | None = Field(
        None,
        description="Correo electrónico de la cuenta. Nulo si la cuenta no "
        "tiene email: el email es opcional en el modelo.",
    )
    nombres: str | None = Field(
        None,
        description="Nombres de la persona vinculada. Nulos si la cuenta no "
        "tiene persona.",
    )
    apellidos: str | None = Field(
        None,
        description="Apellidos de la persona vinculada. Nulos si la cuenta no "
        "tiene persona.",
    )


class SesionRolOut(BaseSchema):
    """Bloque ESPECÍFICO: los hechos de rol que publica el BACKEND.

    Son la autoridad del servidor, no una了好几 del cliente: el frontend
    los pinta y el backend los vuelve a evaluar en cada petición
    (`contratos/02` §3 — "no confiar en una cookie de rol").
    """

    rol: str = Field(
        ...,
        description="Rol funcional de negocio: normal, administrador o sin_rol.",
    )
    grupos: list[str] = Field(
        ...,
        description="Grupos Django del actor. Los dos funcionales son "
        "Normal y Administrador (FR-03 §1.2).",
    )
    es_admin: bool = Field(
        ...,
        description="Si el actor puede entrar al área de administración "
        "(is_staff OR is_superuser).",
    )
    is_staff: bool = Field(..., description="Si el actor es staff operativo.")
    is_superuser: bool = Field(
        ...,
        description="Si el actor tiene el nivel técnico de break-glass.",
    )
    nivel: str = Field(
        ...,
        description="Nivel de privilegio: usuario, staff o superusuario.",
    )
    capacidades: list[str] = Field(
        ...,
        description="Capacidades administrativas del actor (espejo de "
        "core/capacidades.py).",
    )


class SesionUsuarioOut(SesionIdentidadOut, SesionCuentaOut, SesionRolOut):
    """Wrapper único de la sesión: el login y `/auth/me` lo comparten."""


class LoginTokenOut(BaseSchema):
    """Respuesta del inicio de sesión: tokens y hechos de sesión."""

    access_token: str = Field(..., description="Token JWT de acceso.")
    refresh_token: str = Field(..., description="Token JWT de refresco.")
    expires_at: datetime = Field(
        ...,
        description="Instante de expiración del token de acceso (ISO 8601).",
    )
    user: SesionUsuarioOut = Field(..., description="Hechos de sesión del actor.")


__all__ = [
    "LoginDniIn",
    "LoginEmailIn",
    "LoginTokenOut",
    "LoginUsernameIn",
    "SesionCuentaOut",
    "SesionIdentidadOut",
    "SesionRolOut",
    "SesionUsuarioOut",
]
