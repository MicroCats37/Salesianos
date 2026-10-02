"""
Factories — helper functions for building registration payloads.

NOT fixtures — pure Python functions that return dicts.
No DB, no pytest dependency.
"""
import uuid
from typing import Literal


def _unique_email() -> str:
    """Generate a unique email per call to avoid test isolation conflicts."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def _unique_document(tipo: Literal["DNI", "CE", "PAS"]) -> str:
    """Generate a unique document number per call based on document type."""
    if tipo == "DNI":
        return f"{uuid.uuid4().int % 100000000:08d}"
    if tipo == "CE":
        return f"{uuid.uuid4().int % 1000000000:09d}"
    # PAS: min 4 alphanumeric
    return f"PS{uuid.uuid4().hex[:4].upper()}"


def make_payload_registro(
    *,
    email: str | None = None,
    password: str = "testpass123",
    confirmPassword: str = "testpass123",
    tipoDocumento: Literal["DNI", "CE", "PAS"] = "DNI",
    numeroDocumento: str | None = None,
    nombres: str = "Juan",
    apellidos: str = "Pérez",
    genero: Literal["M", "F"] = "M",
    aceptacionVersion: str = "BASES-SF26-2026-09-06",
    acceptedBases: bool = True,
    telefono: str | None = None,
    whatsapp: str | None = None,
    contactoEmergenciaNombre: str | None = None,
    contactoEmergenciaTelefono: str | None = None,
    **kwargs
):
    """Build a valid registration payload with defaults.

    Args:
        email: User email (auto-generated per call if not provided)
        password: Plain text password (will be hashed by backend)
        confirmPassword: Must match password
        tipoDocumento: DNI, CE, or PAS
        numeroDocumento: Document number (validated by tipoDocumento rules;
                        auto-generated per call if not provided)
        nombres: First name(s)
        apellidos: Last name(s)
        genero: M or F
        aceptacionVersion: Version string for accepted bases
        acceptedBases: Must be True
        telefono: Optional 9-digit phone
        whatsapp: Optional 9-digit WhatsApp
        contactoEmergenciaNombre: Optional emergency contact name
        contactoEmergenciaTelefono: Optional 9-digit emergency phone
        **kwargs: Additional fields passed through

    Returns:
        dict: Registration payload ready for POST /auth/register
    """
    # Resolve defaults lazily per call to ensure uniqueness across tests
    _email = email if email is not None else _unique_email()
    _numeroDocumento = numeroDocumento if numeroDocumento is not None else _unique_document(tipoDocumento)

    defaults = {
        "email": _email,
        "password": password,
        "confirmPassword": confirmPassword,
        "tipoDocumento": tipoDocumento,
        "numeroDocumento": _numeroDocumento,
        "nombres": nombres,
        "apellidos": apellidos,
        "genero": genero,
        "aceptacionVersion": aceptacionVersion,
        "acceptedBases": acceptedBases,
    }
    if telefono is not None:
        defaults["telefono"] = telefono
    if whatsapp is not None:
        defaults["whatsapp"] = whatsapp
    if contactoEmergenciaNombre is not None:
        defaults["contactoEmergenciaNombre"] = contactoEmergenciaNombre
    if contactoEmergenciaTelefono is not None:
        defaults["contactoEmergenciaTelefono"] = contactoEmergenciaTelefono
    defaults.update(kwargs)
    return defaults


def make_payload_registro_dni(numero: str = "12345678", **overrides):
    """Registration payload with valid DNI (8 digits)."""
    return make_payload_registro(tipoDocumento="DNI", numeroDocumento=numero, **overrides)


def make_payload_registro_ce(numero: str = "123456789", **overrides):
    """Registration payload with valid CE (9 digits)."""
    return make_payload_registro(tipoDocumento="CE", numeroDocumento=numero, **overrides)


def make_payload_registro_pas(numero: str = "AB1234", **overrides):
    """Registration payload with valid PAS (min 4 alphanumeric, uppercase)."""
    return make_payload_registro(tipoDocumento="PAS", numeroDocumento=numero, **overrides)
