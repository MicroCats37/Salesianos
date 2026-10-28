"""
HTTP wrappers of the accounts (A13, A14).

The wrapper is READ-ONLY and declares NO credential: no password, no hash and
no token.

The tier of the account IS published (`is_staff`, `is_superuser`, `nivel`): an
account administrator must be able to see who holds the break-glass tier.
The surface stays read-only — it never promotes, demotes nor deactivates.
"""
from datetime import datetime
from typing import Optional

from core.types import BaseSchema


class AdminUsuarioListItemOut(BaseSchema):
    """An account with its civil identity and its admin tier."""

    id: str
    username: str
    email: Optional[str] = None
    nombres: str
    apellidos: str
    persona_id: str
    persona_documento: str
    es_admin: bool
    is_staff: bool = False
    is_superuser: bool = False
    nivel: str = "usuario"
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime


class AdminUsuarioInscripcionOut(BaseSchema):
    """A registration owned by the account, inside the active event."""

    inscripcion_id: str
    estado: str
    created_at: datetime


class AdminUsuarioDetailOut(AdminUsuarioListItemOut):
    """The drilldown of an account (A14)."""

    personas: list[AdminUsuarioInscripcionOut] = []


__all__ = [
    "AdminUsuarioListItemOut",
    "AdminUsuarioInscripcionOut",
    "AdminUsuarioDetailOut",
]
