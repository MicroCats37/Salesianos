"""
Factories — helper functions to build valid API payloads for inscripciones.

NOT fixtures — pure Python functions returning dicts.
No DB, no pytest dependency.
"""
import uuid


def _unique_document() -> str:
    """Generate a unique DNI number per call."""
    return f"{uuid.uuid4().int % 100000000:08d}"


def _unique_email() -> str:
    """Generate a unique email per call."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def _unique_evento_nombre() -> str:
    """Generate a unique event name per call."""
    return f"Evento Test {uuid.uuid4().hex[:6]}"


def _unique_paquete_nombre() -> str:
    """Generate a unique package name per call."""
    return f"Paquete Test {uuid.uuid4().hex[:6]}"


def _unique_disciplina_nombre() -> str:
    """Generate a unique discipline name per call."""
    return f"Disciplina Test {uuid.uuid4().hex[:6]}"


def _unique_equipo_nombre() -> str:
    """Generate a unique team name per call."""
    return f"Equipo {uuid.uuid4().hex[:6]}"


# ── Registration / Persona Factories ────────────────────────────────────────────


def make_payload_registro(
    *,
    email: str | None = None,
    password: str = "testpass123",
    confirmPassword: str = "testpass123",
    tipoDocumento: str = "DNI",
    numeroDocumento: str | None = None,
    nombres: str = "Juan",
    apellidos: str = "Pérez",
    genero: str = "M",
    aceptacionVersion: str = "BASES-SF26-2026-09-06",
    acceptedBases: bool = True,
    telefono: str | None = None,
    whatsapp: str | None = None,
    contactoEmergenciaNombre: str | None = None,
    contactoEmergenciaTelefono: str | None = None,
    **kwargs
):
    """Build a valid registration payload (same as usuarios factory).

    Returns:
        dict: Registration payload ready for POST /api/auth/register
    """
    _email = email if email is not None else _unique_email()
    _numeroDocumento = numeroDocumento if numeroDocumento is not None else _unique_document()

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


# ── Inscripcion Payload Factories ──────────────────────────────────────────────


def make_participante_payload(
    *,
    persona_id: str | None = None,
    tipoDocumento: str | None = None,
    numeroDocumento: str | None = None,
    nombres: str | None = None,
    apellidos: str | None = None,
    genero: str | None = None,
    telefono: str | None = None,
    whatsapp: str | None = None,
    rol: str = "JUGADOR",
    talle_camiseta: str | None = None,
) -> dict:
    """
    Build a participante sub-payload for equipo creation.

    Supports two modes:
    - Legacy: pass persona_id (existing Persona UUID).
    - Inline: pass tipoDocumento + numeroDocumento + nombres + apellidos + genero.

    Exactly one mode must be used.
    """
    if persona_id is not None:
        result = {"persona_id": persona_id, "rol": rol}
    else:
        result = {
            "tipoDocumento": tipoDocumento or "DNI",
            "numeroDocumento": numeroDocumento or _unique_document(),
            "nombres": nombres or "Juan",
            "apellidos": apellidos or "Pérez",
            "genero": genero or "M",
            "rol": rol,
        }
    if telefono is not None:
        result["telefono"] = telefono
    if whatsapp is not None:
        result["whatsapp"] = whatsapp
    if talle_camiseta is not None:
        result["talle_camiseta"] = talle_camiseta
    return result


def make_equipo_payload(
    disciplina_id: str,
    nombre: str | None = None,
    participantes: list[dict] | None = None,
) -> dict:
    """Build an equipo sub-payload for inscription creation.

    `categoria_id` is sent as `null` (wizard does not resolve categorias yet).
    """
    return {
        "disciplina_id": disciplina_id,
        "categoria_id": None,
        "nombre": nombre if nombre is not None else _unique_equipo_nombre(),
        "participantes": participantes or [],
    }


def make_inscripcion_payload(
    paquete_id: str,
    promocion_id: str,
    observacion: str | None = None,
    equipos: list[dict] | None = None,
    fusion_promocion_id: str | None = None,
) -> dict:
    """Build a full inscription creation payload.

    Note: `evento_id` is NOT part of the public payload — the active event
    is resolved by the backend from `settings.EVENTO_ACTIVO_NOMBRE`.

    Args:
        paquete_id: str — Paquete.id
        promocion_id: str — Promocion.id
        observacion: str | None — optional observation
        equipos: list[dict] — list of equipo payloads (from make_equipo_payload)
        fusion_promocion_id: str | None — optional Promocion.id for fusion

    Returns:
        dict — payload ready for POST /api/inscripciones/
    """
    result = {
        "paquete_id": paquete_id,
        "promocion_id": promocion_id,
        "observacion": observacion,
        "equipos": equipos or [],
    }
    if fusion_promocion_id is not None:
        result["fusion_promocion_id"] = fusion_promocion_id
    return result
