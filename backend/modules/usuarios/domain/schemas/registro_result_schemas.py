"""
RegistroResult — DTOs internos para el flujo de registro de usuarios.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class RegistroUserResult(BaseModel):
    """DTO de resultado interno con datos del usuario creado."""
    id: uuid.UUID
    username: str
    email: str | None
    is_staff: bool
    is_superuser: bool
    persona_id: uuid.UUID | None = None


class RegistroTokenResult(BaseModel):
    """DTO de resultado para operaciones de registro — contiene tokens y datos del usuario."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    user: RegistroUserResult