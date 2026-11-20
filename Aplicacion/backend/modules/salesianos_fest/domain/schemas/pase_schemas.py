"""DTOs internos del dominio de PASES.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6

Son DTOs de Pydantic **puros** (no schemas HTTP). Reflejan lo que la capa
de servicios necesita, NO lo que el cliente HTTP envía.

Reglas que se respetan aquí:

- **El precio NO viaja** (`RN-C02`): ningún DTO de compra acepta un importe.
  El servidor lo resuelve contra el catálogo vigente y lo congela.
- **El DNI NO es una credencial** (`RN-U04`, `contratos/02` §5): un DTO
  declara QUIÉN es la persona, nunca QUÉ puede hacer. La autorización se
  decide con el actor o con el token del enlace.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ComprarPaseData(BaseModel):
    """La intención de comprar pases.

    El comprador es una identidad CIVIL: puede no tener cuenta
    (`FL-06` paso 2). El servidor resuelve o registra la `Persona`; este
    paquete NO crea un `Usuario` nunca.

    **`persona_id` es la identidad YA RESUELTA del comprador.** Cuando viaja,
    el comprador es esa persona y el servidor NO vuelve a resolverlo ni a
    registrarlo. Lo usa el comando administrativo de compra asistida, que
    resuelve la identidad del CLIENTE una sola vez y la declara aquí para que
    la compra NEVER se atribuya a la cuenta del administrador. La ruta pública
    NO lo expone: el documento de identidad no es una credencial (`RN-U04`).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    persona_id: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Identificador de la persona del padrón ya resuelta. Si viaja, el "
            "comprador es esa persona."
        ),
    )
    pase_id: str = Field(
        ...,
        max_length=64,
        description="Pase del catálogo que se compra.",
    )
    cantidad: int = Field(
        ...,
        ge=1,
        description="Número de pases que se compran.",
    )
    tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento del comprador.",
    )
    numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento del comprador.",
    )
    nombres: str = Field(
        ...,
        max_length=255,
        description="Nombres del comprador.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos del comprador.",
    )
    contacto_email: str = Field(
        default="",
        max_length=255,
        description="Correo de contacto. No habilita ningún derecho.",
    )

    @field_validator("nombres")
    @classmethod
    def _exigir_nombres(cls, valor: str) -> str:
        """El nombre del comprador es obligatorio."""
        if not str(valor or "").strip():
            raise ValueError("El nombre del comprador es obligatorio.")
        return str(valor).strip()


class AsignarBeneficiarioData(BaseModel):
    """La intención de asignar un pase comprado a una persona.

    La persona puede llegar por IDENTIFICADOR (ya está en el padrón) o por
    DOCUMENTO (se resuelve o registra). La resolución la hace
    `usuarios`: este módulo NO crea identidades por su cuenta.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    persona_id: str | None = Field(
        default=None,
        max_length=64,
        description="Identificador de la persona del padrón, si se conoce.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=3,
        description="Tipo de documento del beneficiario.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento del beneficiario.",
    )
    nombres: str = Field(
        default="",
        max_length=255,
        description="Nombres del beneficiario si se resuelve por documento.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos del beneficiario si se resuelve por documento.",
    )
    motivo: str = Field(
        default="",
        max_length=500,
        description="Motivo de la asignación. Opcional en una compra.",
    )


class RevocarBeneficiarioData(BaseModel):
    """La intención de revocar un derecho de entrada."""

    model_config = ConfigDict(str_strip_whitespace=True)

    motivo: str = Field(
        default="",
        max_length=500,
        description="Motivo de la revocación. Se conserva en la auditoría.",
    )


class OtorgarCortesiaData(BaseModel):
    """La intención de otorgar una cortesía.

    El MOTIVO es obligatorio (`RN-P05`) y el ACTOR lo pone el servidor: es la
    cuenta autenticada del administrador que hace la operación.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    edicion_id: str = Field(
        ...,
        max_length=64,
        description="Edición del alcance de la cortesía (`FL-07` paso 1).",
    )
    pase_id: str = Field(
        ...,
        max_length=64,
        description="Pase del catálogo que se otorga.",
    )
    persona_id: str | None = Field(
        default=None,
        max_length=64,
        description="Identificador de la persona del padrón, si se conoce.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento de la persona.",
    )
    nombres: str = Field(
        default="",
        max_length=255,
        description="Nombres de la persona si se resuelve por documento.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos de la persona si se resuelve por documento.",
    )
    motivo: str = Field(
        ...,
        max_length=500,
        description="Motivo del otorgamiento. Obligatorio.",
    )


__all__ = [
    "AsignarBeneficiarioData",
    "ComprarPaseData",
    "OtorgarCortesiaData",
    "RevocarBeneficiarioData",
]
