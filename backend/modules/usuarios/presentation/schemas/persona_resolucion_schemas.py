"""
HTTP schemas of the exact identity lookup of an existing `Persona`.

The wrapper is EXPLICIT field by field: it carries ONLY what the caller needs
to confirm the identity and to assign an existing right. The account state,
the contacts, the address and the QR credential NEVER travel
(`contract/api-wrapper-presenter-contract.md` §6).
"""

from core.types import BaseSchema


class PersonaResueltaOut(BaseSchema):
    """
    The person that matches the consulted civil identity EXACTLY.

    `numero_documento` is the document the caller already supplied: it is
    returned unaltered so the client can confirm the match without the server
    revealing any other datum of the person.
    """

    persona_id: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str


__all__ = ["PersonaResueltaOut"]
