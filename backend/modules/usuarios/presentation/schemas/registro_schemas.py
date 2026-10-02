"""
Esquemas HTTP request/response para Registro — Schema Ninja para API.
"""
import re
import uuid
from datetime import datetime
from ninja import Field
from pydantic import field_validator, model_validator
from typing import Literal

from core.types import BaseSchema


class RegisterIn(BaseSchema):
    """Payload de registro de usuario responsable."""
    email: str = Field(..., max_length=120, description="Correo electrónico")
    password: str = Field(..., min_length=8, max_length=120, description="Contraseña (mínimo 8 caracteres)")
    confirmPassword: str = Field(..., description="Confirmación de contraseña (debe coincidir con password)")
    tipoDocumento: Literal["DNI", "CE", "PAS"] = Field(..., description="Tipo de documento de identidad")
    numeroDocumento: str = Field(..., min_length=1, max_length=20, description="Número de documento")
    nombres: str = Field(..., max_length=120, description="Nombres")
    apellidos: str = Field(..., max_length=120, description="Apellidos")
    genero: Literal["M", "F"] = Field(..., description="Género (M=Masculino, F=Femenino)")
    telefono: str | None = Field(None, min_length=9, max_length=9, description="Teléfono (9 dígitos)")
    whatsapp: str | None = Field(None, min_length=9, max_length=9, description="WhatsApp (9 dígitos)")
    contactoEmergenciaNombre: str | None = Field(None, max_length=120, description="Nombre de contacto de emergencia")
    contactoEmergenciaTelefono: str | None = Field(None, min_length=9, max_length=9, description="Teléfono de emergencia (9 dígitos)")
    acceptedBases: bool = Field(..., description="Debe ser true para aceptar las bases")

    @model_validator(mode="after")
    def passwords_must_match(self):
        """Valida que password y confirmPassword coincidan."""
        if self.password != self.confirmPassword:
            raise ValueError("Las contraseñas no coinciden")
        return self

    @field_validator("acceptedBases")
    @classmethod
    def bases_must_be_accepted(cls, v):
        """acceptedBases debe ser True."""
        if not v:
            raise ValueError("Debe aceptar las bases del evento")
        return v

    @field_validator("numeroDocumento", mode="after")
    @classmethod
    def validar_numero_documento(cls, v, info):
        """Valida formato de número de documento según tipo (DNI=8 dígitos, CE=9 dígitos, PAS=mín 4 alfanum)."""
        tipo = info.data.get("tipoDocumento")
        if not tipo:
            return v  # tipoDocumento validation will catch missing/invalid type

        v = v.strip()
        if tipo == "DNI":
            if not re.fullmatch(r"\d{8}", v):
                raise ValueError("DNI debe contener exactamente 8 dígitos")
        elif tipo == "CE":
            if not re.fullmatch(r"\d{9}", v):
                raise ValueError("CE debe contener exactamente 9 dígitos")
        elif tipo == "PAS":
            if not re.fullmatch(r"[A-Za-z0-9]{4,}", v):
                raise ValueError("PAS debe contener mínimo 4 caracteres alfanuméricos")
            v = v.upper()  # Normalize passport to uppercase

        return v


class RegistroUserOut(BaseSchema):
    """Datos de usuario en respuesta de registro."""
    id: uuid.UUID = Field(..., description="ID único del usuario")
    username: str = Field(..., description="Nombre de usuario generado")
    email: str | None = Field(None, description="Correo electrónico")
    is_staff: bool = Field(..., description="Es staff")
    is_superuser: bool = Field(..., description="Es superusuario")
    persona_id: uuid.UUID | None = Field(None, description="ID de persona asociada")


class RegisterOut(BaseSchema):
    """Respuesta de registro con tokens y datos del usuario."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_at: datetime = Field(..., description="Fecha/hora de expiración del access token (ISO 8601)")
    user: RegistroUserOut = Field(..., description="Datos del usuario registrado")