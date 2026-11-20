"""
DTO interno del ALTA DE UNA CUENTA con su identidad.

`contract/django-app-architecture-contract.md` §4.6: los DTOs de `domain/`
reflejan lo que la capa de servicios necesita, NO lo que el cliente HTTP
envía. El payload HTTP vive en `presentation/schemas/auth_schemas.py`
(`RegisterIn`) y se traduce aquí.

La identidad se reutiliza tal cual: el DTO de la persona es el MISMO
`PersonaCreateData` que usa el resto del módulo, con sus normalizaciones
(`normalizar_tipo_documento`, `normalizar_numero_documento`). Así el documento
se persiste y se compara siempre en la misma forma (`FR-03` §1.1).
"""

from pydantic import BaseModel, ConfigDict, field_validator

from modules.usuarios.domain.schemas import PersonaCreateData


class RegistroData(BaseModel):
    """Los datos del alta de una cuenta y de su identidad.

    `email` es la clave ÚNICA y NO NULA de la cuenta
    (`unique_email_usuario_no_vacio`): se compara sin distinguir mayúsculas,
    igual que hace el inicio de sesión (`FR-03` §1.2).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    persona: PersonaCreateData
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _exigir_email(cls, valor: str) -> str:
        if not str(valor or "").strip():
            raise ValueError("El correo electrónico es obligatorio.")
        return str(valor).strip()

    @field_validator("password")
    @classmethod
    def _exigir_password(cls, valor: str) -> str:
        if not str(valor or ""):
            raise ValueError("La contraseña es obligatoria.")
        return str(valor)


__all__ = ["RegistroData"]
