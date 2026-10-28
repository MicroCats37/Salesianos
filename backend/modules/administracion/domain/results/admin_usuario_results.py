"""
Result DTOs of the accounts (A13, A14).

The account surface is READ-ONLY and NEVER carries a credential:

- `password` / `password_hash` — NEVER,
- any token (access, refresh, session) — NEVER.

The tier of the account IS surfaced (`is_staff`, `is_superuser`, `nivel`): an
account administrator must be able to SEE who holds the break-glass tier. The
surface remains read-only: it never promotes, demotes nor deactivates anyone.

The civil identity lives in the linked `Persona`; the account carries only the
login data plus the identity block the surface needs.
"""

from datetime import datetime

from pydantic import BaseModel


class AdminUsuarioListItemResult(BaseModel):
    """An account with its civil identity and its admin tier."""

    id: str
    username: str
    email: str | None = None
    nombres: str
    apellidos: str
    persona_id: str
    persona_documento: str
    es_admin: bool
    is_staff: bool = False
    is_superuser: bool = False
    nivel: str = "usuario"
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime


class AdminUsuarioInscripcionResult(BaseModel):
    """A registration owned by the account, inside the active event."""

    inscripcion_id: str
    estado: str
    created_at: datetime


class AdminUsuarioDetalleResult(AdminUsuarioListItemResult):
    """The drilldown of an account (A14)."""

    personas: list[AdminUsuarioInscripcionResult] = []


__all__ = [
    "AdminUsuarioListItemResult",
    "AdminUsuarioInscripcionResult",
    "AdminUsuarioDetalleResult",
]
