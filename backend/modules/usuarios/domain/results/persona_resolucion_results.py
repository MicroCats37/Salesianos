"""Persona resolution results — DTO of the exact identity lookup."""

from dataclasses import dataclass


@dataclass
class PersonaResueltaResult:
    """
    The person that matches the consulted civil identity EXACTLY.

    It carries ONLY the fields needed to confirm the identity and to assign
    an existing right: the internal id, the display name, the document type
    and the document number the caller already supplied.
    """

    persona_id: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
