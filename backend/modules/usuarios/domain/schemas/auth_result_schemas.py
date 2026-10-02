"""
Esquemas de resultado de dominio para Auth — DTOs internos usados por servicios, NO esquemas HTTP.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class AuthUserResult(BaseModel):
    """DTO de resultado interno con datos de usuario para generación de tokens."""
    id: uuid.UUID
    username: str
    email: str | None
    is_staff: bool
    is_superuser: bool
    # Persona relation - may be None for legacy users
    persona_id: uuid.UUID | None = None
    dni_legacy: str | None = None  # Old DNI field kept for compatibility


class LoginTokenResult(BaseModel):
    """DTO de resultado para operaciones de login — contiene tokens y datos del usuario."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    user: AuthUserResult
