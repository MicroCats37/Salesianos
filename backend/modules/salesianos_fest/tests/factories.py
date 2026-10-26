"""Factories for salesianos_fest tests — pure dict builders (NOT pytest fixtures)."""
from datetime import date
from decimal import Decimal


def make_evento_payload(
    nombre: str = "Salesianos FEST 2026",
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    esta_activo: bool = True,
    **kwargs,
) -> dict:
    """Build an Evento payload dict."""
    return {
        "nombre": nombre,
        "fecha_inicio": fecha_inicio or date(2026, 11, 15),
        "fecha_fin": fecha_fin or date(2026, 11, 20),
        "esta_activo": esta_activo,
        **kwargs,
    }


def make_disciplina_payload(
    nombre: str = "Fútbol 7 Masculino",
    sigla: str = "F7M",
    modalidad: str = "M",
    min_jugadores: int = 7,
    max_jugadores: int = 10,
    esta_activa: bool = True,
    **kwargs,
) -> dict:
    """Build a Disciplina payload dict."""
    return {
        "nombre": nombre,
        "sigla": sigla,
        "modalidad": modalidad,
        "min_jugadores": min_jugadores,
        "max_jugadores": max_jugadores,
        "esta_activa": esta_activa,
        **kwargs,
    }


def make_promocion_payload(
    anio: int = 2012,
    nombre: str = "Junior",
    activa: bool = True,
    **kwargs,
) -> dict:
    """Build a Promocion payload dict."""
    return {
        "anio": anio,
        "nombre": nombre,
        "activa": activa,
        **kwargs,
    }


def make_categoria_payload(
    evento_id: str | None = None,
    nombre: str = "Senior",
    promocion_desde: int = 1998,
    promocion_hasta: int = 2005,
    esta_activa: bool = True,
    **kwargs,
) -> dict:
    """Build a Categoria payload dict."""
    payload = {
        "nombre": nombre,
        "promocion_desde": promocion_desde,
        "promocion_hasta": promocion_hasta,
        "esta_activa": esta_activa,
    }
    if evento_id is not None:
        payload["evento_id"] = str(evento_id)
    return {**payload, **kwargs}


def make_paquete_payload(
    evento_id: str | None = None,
    nombre: str = "Reencuentro + Fiesta",
    descripcion: str = "Pack con fiesta",
    tipo: str = "PACK",
    modo_disciplinas: str = "ELEGIBLE",
    cantidad_disciplinas: int = 1,
    minimo_compra_inicial: int = 10,
    activo: bool = True,
    **kwargs,
) -> dict:
    """Build a Paquete payload dict."""
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "tipo": tipo,
        "modo_disciplinas": modo_disciplinas,
        "cantidad_disciplinas": cantidad_disciplinas,
        "minimo_compra_inicial": minimo_compra_inicial,
        "activo": activo,
    }
    if evento_id is not None:
        payload["evento_id"] = str(evento_id)
    return {**payload, **kwargs}


def make_paquete_precio_payload(
    paquete_id: str | None = None,
    etapa: str = "PREVENTA",
    precio_unitario: Decimal | str = "40.00",
    vigente_desde: date | None = None,
    vigente_hasta: date | None = None,
    activo: bool = True,
    **kwargs,
) -> dict:
    """Build a PaquetePrecio payload dict."""
    payload = {
        "etapa": etapa,
        "precio_unitario": precio_unitario,
        "vigente_desde": vigente_desde or date.today(),
        "vigente_hasta": vigente_hasta,
        "activo": activo,
    }
    if paquete_id is not None:
        payload["paquete_id"] = str(paquete_id)
    return {**payload, **kwargs}


def make_paquete_beneficio_payload(
    paquete_id: str | None = None,
    tipo: str = "FIESTA",
    cantidad: int = 1,
    alcance: str = "INDIVIDUAL",
    modo_calculo: str = "FIJO_INICIAL",
    **kwargs,
) -> dict:
    """Build a PaqueteBeneficio payload dict."""
    payload = {
        "tipo": tipo,
        "cantidad": cantidad,
        "alcance": alcance,
        "modo_calculo": modo_calculo,
    }
    if paquete_id is not None:
        payload["paquete_id"] = str(paquete_id)
    return {**payload, **kwargs}


def make_paquete_disciplina_payload(
    paquete_id: str | None = None,
    disciplina_id: str | None = None,
    **kwargs,
) -> dict:
    """Build a PaqueteDisciplina payload dict."""
    payload = {}
    if paquete_id is not None:
        payload["paquete_id"] = str(paquete_id)
    if disciplina_id is not None:
        payload["disciplina_id"] = str(disciplina_id)
    return {**payload, **kwargs}


def make_inscripcion_payload(
    evento_id: str | None = None,
    responsable_id: str | None = None,
    paquete_id: str | None = None,
    promocion_id: str | None = None,
    fusion_promocion_id: str | None = None,
    delegado_id: str | None = None,
    estado: str = "BORRADOR",
    observacion: str = "",
    **kwargs,
) -> dict:
    """Build an Inscripcion payload dict."""
    payload = {
        "evento_id": str(evento_id) if evento_id else None,
        "responsable_id": str(responsable_id) if responsable_id else None,
        "paquete_id": str(paquete_id) if paquete_id else None,
        "promocion_id": str(promocion_id) if promocion_id else None,
        "estado": estado,
        "observacion": observacion,
    }
    if fusion_promocion_id:
        payload["fusion_promocion_id"] = str(fusion_promocion_id)
    if delegado_id:
        payload["delegado_id"] = str(delegado_id)
    return {**payload, **kwargs}


def make_equipo_payload(
    inscripcion_id: str | None = None,
    disciplina_id: str | None = None,
    nombre: str = "Los Tigres FC",
    estado: str = "EQUIPO_ACTIVO",
    **kwargs,
) -> dict:
    """Build an Equipo payload dict."""
    payload = {
        "inscripcion_id": str(inscripcion_id) if inscripcion_id else None,
        "disciplina_id": str(disciplina_id) if disciplina_id else None,
        "nombre": nombre,
        "estado": estado,
    }
    return {**payload, **kwargs}


def make_inscripcion_persona_payload(
    inscripcion_id: str | None = None,
    persona_id: str | None = None,
    estado: str = "A",
    **kwargs,
) -> dict:
    """Build an InscripcionPersona payload dict."""
    payload = {
        "inscripcion_id": str(inscripcion_id) if inscripcion_id else None,
        "persona_id": str(persona_id) if persona_id else None,
        "estado": estado,
    }
    return {**payload, **kwargs}


def make_participacion_payload(
    inscripcion_persona_id: str | None = None,
    equipo_id: str | None = None,
    rol: str = "J",
    talla_camiseta: str = "M",
    notas: str = "",
    estado: str = "A",
    **kwargs,
) -> dict:
    """Build a Participacion payload dict."""
    payload = {
        "inscripcion_persona_id": str(inscripcion_persona_id) if inscripcion_persona_id else None,
        "equipo_id": str(equipo_id) if equipo_id else None,
        "rol": rol,
        "talla_camiseta": talla_camiseta,
        "notas": notas,
        "estado": estado,
    }
    return {**payload, **kwargs}


def make_actualizar_inscripcion_payload(
    estado: str | None = None,
    observacion: str | None = None,
    delegado_id: str | None = None,
    **kwargs,
) -> dict:
    """Build an ActualizarInscripcion payload dict (PATCH /inscripciones/{id})."""
    payload = {
        "estado": estado,
        "observacion": observacion,
        "delegado_id": str(delegado_id) if delegado_id else None,
    }
    return {**payload, **kwargs}


def make_acreditacion_override_payload(
    autorizacion: str = "BLOQUEADA",
    motivo: str = "Revision del comite del evento",
    **kwargs,
) -> dict:
    """Build an OverrideFiesta payload dict (admin-only override)."""
    payload = {
        "autorizacion": autorizacion,
        "motivo": motivo,
    }
    return {**payload, **kwargs}

