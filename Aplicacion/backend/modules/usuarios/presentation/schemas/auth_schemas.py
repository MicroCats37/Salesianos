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

import re
from datetime import datetime
from typing import Literal

from core.types import BaseSchema
from ninja import Field
from pydantic import field_validator, model_validator


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


class RegisterIn(BaseSchema):
    """Entrada del alta de una cuenta con su identidad.

    Los NOMBRES de los campos son los que el CLIENTE envía: son camelCase
    (`tipoDocumento`, `numeroDocumento`, `acceptedBases`) porque el espejo del
    frontend (`features/auth/schemas/register.schema.ts`) congeló ese payload.
    El resto de la API del módulo habla en snake_case.

    Las reglas que se validan AQUÍ son las del CONTRATO HTTP, no las del
    dominio: la coincidencia de las contraseñas, la aceptación de las bases y
    el FORMATO del número de documento según su tipo. La normalización y el
    vocabulario del documento los aplica el dominio
    (`modules/usuarios/domain/schemas/`).
    """

    email: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Correo electrónico de la cuenta.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=120,
        description="Contraseña de la cuenta.",
    )
    confirmPassword: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Confirmación de la contraseña.",
    )
    tipoDocumento: Literal["DNI", "CE", "PAS"] = Field(
        ...,
        description="Tipo de documento de identidad.",
    )
    numeroDocumento: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Número de documento de identidad.",
    )
    nombres: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombres de la persona.",
    )
    apellidos: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Apellidos de la persona.",
    )
    genero: Literal["M", "F"] = Field(..., description="Género de la persona.")
    telefono: str | None = Field(
        None,
        min_length=9,
        max_length=9,
        description="Teléfono de la persona.",
    )
    whatsapp: str | None = Field(
        None,
        min_length=9,
        max_length=9,
        description="WhatsApp de la persona.",
    )
    contactoEmergenciaNombre: str | None = Field(
        None,
        max_length=120,
        description="Nombre del contacto de emergencia.",
    )
    contactoEmergenciaTelefono: str | None = Field(
        None,
        min_length=9,
        max_length=9,
        description="Teléfono del contacto de emergencia.",
    )
    acceptedBases: bool = Field(
        ...,
        description="La aceptación explícita de las bases del evento.",
    )

    @model_validator(mode="after")
    def _las_contrasenas_deben_coincidir(self):
        """La confirmación tiene que ser la MISMA contraseña."""
        if self.password != self.confirmPassword:
            raise ValueError("Las contraseñas no coinciden.")
        return self

    @field_validator("acceptedBases")
    @classmethod
    def _las_bases_deben_aceptarse(cls, valor: bool) -> bool:
        """Las bases se aceptan de forma explícita."""
        if not valor:
            raise ValueError("Debe aceptar las bases del evento.")
        return valor

    @model_validator(mode="after")
    def _validar_documento_segun_tipo(self):
        """Aplica el formato del documento YA CONOCIENDO su tipo.

        **Por qué es `after` y no `before`.** `ninja.Schema` envuelve el
        cuerpo de la petición en un `DjangoGetter` ANTES de ejecutar los
        validadores `before` (`ninja/schema.py::_run_root_validator`). Un
        validador `before` que espera un `dict` NUNCA ve el cuerpo real: se
        salta siempre y la regla se aplicaría de palabra. El validador `after`
        ya tiene los campos validados y tipados, así que la regla se aplica
        DE VERDAD.

        **Por qué se ignoran los separadores.** El dominio normaliza el
        documento (`normalizar_numero_documento`: sin espacios ni guiones, en
        mayúsculas) y la comparación es case-insensitive por construcción
        (`FR-03` §1.1). La capa HTTP comprueba el FORMATO, no el valor
        persistido: repetir aquí la normalización del dominio sería duplicar
        la validación (`contract/django-app-architecture-contract.md` §10).
        """
        numero = re.sub(r"[\s\-./_]", "", str(self.numeroDocumento or "")).upper()

        if self.tipoDocumento == "DNI":
            if not re.fullmatch(r"\d{8}", numero):
                raise ValueError("El DNI debe contener exactamente 8 dígitos.")
        elif self.tipoDocumento == "CE":
            if not re.fullmatch(r"\d{9}", numero):
                raise ValueError(
                    "El Carnet de Extranjería debe contener exactamente 9 dígitos."
                )
        else:
            if not re.fullmatch(r"[A-Z0-9]{4,}", numero):
                raise ValueError(
                    "El pasaporte debe tener al menos 4 caracteres alfanuméricos."
                )
        return self


__all__ = [
    "LoginDniIn",
    "LoginEmailIn",
    "LoginTokenOut",
    "LoginUsernameIn",
    "RegisterIn",
    "SesionCuentaOut",
    "SesionIdentidadOut",
    "SesionRolOut",
    "SesionUsuarioOut",
]
