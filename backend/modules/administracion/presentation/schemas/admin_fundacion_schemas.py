"""
AdminHealthOut — HTTP wrapper of the administration foundation probe.

Explicit named wrapper, never a generic `data`/`contexto` envelope
(`contract/api-wrapper-presenter-contract.md` §5). No secret, no credential
and no internal identifier of a business entity is exposed here.
"""

from typing import Optional

from ninja import Schema


class AdminHealthOut(Schema):
    """State of the administration module for an authorized administrator."""

    modulo: str
    estado: str
    evento_activo_id: Optional[str] = None
    evento_activo_nombre: Optional[str] = None


__all__ = ["AdminHealthOut"]
