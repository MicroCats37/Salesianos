"""
Validation helpers for business rules in the inscripciones module.

These are pure functions that validate business rules without touching the ORM.
They are meant to be called from core services.
"""

from modules.inscripciones.domain.models import (
    Disciplina,
    Paquete,
    PaqueteDisciplina,
    ParticipacionDisciplina,
    Inscripcion,
    EquipoInscrito,
)
from modules.inscripciones.domain.constants import ModoDisciplinasPaqueteChoices


def validar_roster_equipo(disciplina: Disciplina, cantidad_jugadores: int) -> list[str]:
    """
    Validate team roster against discipline min/max players.

    Args:
        disciplina: The Disciplina instance with min/max constraints.
        cantidad_jugadores: Current number of players in the team.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    if disciplina.min_jugadores is not None and cantidad_jugadores < disciplina.min_jugadores:
        errors.append(
            f"El equipo necesita al menos {disciplina.min_jugadores} jugadores "
            f"({cantidad_jugadores} actuales)."
        )
    if disciplina.max_jugadores is not None and cantidad_jugadores > disciplina.max_jugadores:
        errors.append(
            f"El equipo no puede exceder {disciplina.max_jugadores} jugadores "
            f"({cantidad_jugadores} actuales)."
        )
    return errors


def validar_disciplina_en_paquete(
    paquete: Paquete,
    disciplina: Disciplina | str,
) -> bool:
    """
    Check if a discipline is included in a package.

    Accepts either a `Disciplina` instance or a `disciplina_id` (str).

    Args:
        paquete: The Paquete instance.
        disciplina: Disciplina instance or its UUID string.

    Returns:
        True if discipline is in package, False otherwise.
    """
    disciplina_id = getattr(disciplina, "id", disciplina)
    return PaqueteDisciplina.objects.filter(
        paquete=paquete,
        disciplina_id=disciplina_id,
    ).exists()


def validar_r11_prevent_duplicado(
    evento_id: str,
    disciplina_id: str,
    persona_id: str,
) -> bool:
    """
    Check if a person is already registered in the same discipline+event (R11 pre-check).

    This is the service-layer check (Capa 2) before attempting to create a
    ParticipacionDisciplina. The DB constraint (Capa 1) is the final protection.

    Args:
        evento_id: UUID of the event.
        disciplina_id: UUID of the disciplina.
        persona_id: UUID of the persona.

    Returns:
        True if already exists (should block), False if available.
    """
    return ParticipacionDisciplina.objects.filter(
        evento_id=evento_id,
        disciplina_id=disciplina_id,
        persona_id=persona_id,
    ).exists()


def validar_equipo_duplicado(inscripcion_id: str, disciplina_id: str) -> bool:
    """
    Check if an equipo already exists for the same inscription+discipline (D7).

    Args:
        inscripcion_id: UUID of the inscripcion.
        disciplina_id: UUID of the disciplina.

    Returns:
        True if already exists (should block), False if available.
    """
    return EquipoInscrito.objects.filter(
        inscripcion_id=inscripcion_id,
        disciplina_id=disciplina_id,
    ).exists()


def calcular_cupo_paquete(inscripcion: Inscripcion) -> int:
    """
    Calculate the number of distinct persons in an inscription's package.

    D6 CONFIRMED: counts DISTINCT Persona records across all ParticipacionDisciplina
    linked to the inscription's equipos.

    Args:
        inscripcion: The Inscripcion instance.

    Returns:
        Count of distinct Persona records.
    """
    return (
        ParticipacionDisciplina.objects
        .filter(equipo__inscripcion=inscripcion)
        .values('persona')
        .distinct()
        .count()
    )


def validar_cupo_paquete(inscripcion: Inscripcion, paquete: Paquete) -> list[str]:
    """
    Validate that the inscription does not exceed package capacity.

    Args:
        inscripcion: The Inscripcion instance.
        paquete: The Paquete with cantidad_maxima_participantes.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    total_personas = calcular_cupo_paquete(inscripcion)
    if total_personas > paquete.cantidad_maxima_participantes:
        errors.append(
            f"Se excede la capacidad máxima del paquete: "
            f"{total_personas} personas (máximo {paquete.cantidad_maxima_participantes})."
        )
    return errors


def validar_delegado_es_elegible(
    inscripcion: Inscripcion,
    persona_id: str,
) -> tuple[bool, str]:
    """
    Validate that a persona is eligible to be a delegate.

    Rule: delegate must be either the inscription responsible OR a participant
    in any team belonging to that inscription.

    Args:
        inscripcion: The Inscripcion instance.
        persona_id: UUID of the persona to check.

    Returns:
        Tuple of (is_eligible, reason).
    """
    # Check if responsible
    if str(inscripcion.responsable_id) == str(persona_id):
        return True, "Es el responsable de la inscripción."

    # Check if participant in any equipo
    is_participante = (
        ParticipacionDisciplina.objects
        .filter(
            equipo__inscripcion=inscripcion,
            persona_id=persona_id,
        )
        .exists()
    )
    if is_participante:
        return True, "Es participante en un equipo de la inscripción."

    return False, "No es el responsable ni participante en ningún equipo de la inscripción."


def validar_consistencia_equipo_participacion(
    equipo: EquipoInscrito,
    evento_id: str,
    disciplina_id: str,
) -> list[str]:
    """
    Validate consistency between equipo and participacion fields.

    Args:
        equipo: The EquipoInscrito instance.
        evento_id: Expected evento UUID.
        disciplina_id: Expected disciplina UUID.

    Returns:
        List of error messages (empty if consistent).
    """
    errors = []
    if str(equipo.inscripcion.evento_id) != str(evento_id):
        errors.append(
            f"El equipo no pertenece al evento de la participación "
            f"(equipo.evento={equipo.inscripcion.evento_id}, participación={evento_id})."
        )
    if str(equipo.disciplina_id) != str(disciplina_id):
        errors.append(
            f"El equipo no pertenece a la disciplina de la participación "
            f"(equipo.disciplina={equipo.disciplina_id}, participación={disciplina_id})."
        )
    return errors


def validar_cantidad_disciplinas_paquete(
    paquete: Paquete,
    equipos_data: list[dict],
) -> list[str]:
    """
    Validate that the number of equipos and their discipline selections are valid for the package.

    - Counts total equipos (NOT distinct disciplines) and validates against cantidad_maxima_equipos.
    - This allows duplicate disciplines when the package's capacity allows multiple teams
      with the same discipline (frontend permiteDuplicados=true).
    - Discipline-belongs-to-package is validated per-equipo in crear_inscripcion_flujo.

    For mode FIJO: equipos count must equal the package's discipline count.
    For mode ELEGIBLE: equipos count must not exceed cantidad_disciplinas_requeridas
        (which equals cantidad_maxima_equipos in ELEGIBLE mode).

    Only validates when equipos_data is non-empty (empty initial inscription is allowed).

    Args:
        paquete: The Paquete with modo_disciplinas and cantidad_disciplinas_requeridas.
        equipos_data: List of equipo dicts with disciplina_id keys.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    # If no equipos provided, skip validation (empty initial inscription is allowed)
    if not equipos_data:
        return errors

    modo = getattr(paquete, 'modo_disciplinas', None)

    # If mode is not set or package has no requirement, skip validation
    if not modo:
        return errors

    cantidad_requerida = paquete.cantidad_disciplinas_requeridas
    if cantidad_requerida is None:
        return errors

    # Count total equipos (NOT distinct disciplines — this allows duplicates
    # when package capacity allows multiple teams with the same discipline)
    cantidad_equipos = len(equipos_data)

    if modo == ModoDisciplinasPaqueteChoices.FIJO:
        # For FIJO mode, the package already has fixed disciplines via PaqueteDisciplina.
        # Validate that the number of equipos matches the discipline count in the package.
        # The frontend prevents selecting the same discipline twice in FIJO mode.
        cantidad_disciplinas_paquete = PaqueteDisciplina.objects.filter(
            paquete=paquete
        ).count()
        if cantidad_equipos != cantidad_disciplinas_paquete:
            errors.append(
                f"El paquete '{paquete.nombre}' requiere exactamente {cantidad_disciplinas_paquete} "
                f"equipo(s) (uno por cada disciplina fija), pero se proporcionaron {cantidad_equipos}."
            )
    elif modo == ModoDisciplinasPaqueteChoices.ELEGIBLE:
        # For ELEGIBLE mode, validate equipos count does not exceed cantidad_disciplinas_requeridas.
        # Since cantidad_maxima_equipos == cantidad_disciplinas_requeridas in ELEGIBLE mode,
        # this naturally enforces the team-count limit while allowing duplicates when
        # the frontend permiteDuplicados flag is active.
        if cantidad_equipos > cantidad_requerida:
            errors.append(
                f"El paquete '{paquete.nombre}' permite máximo {cantidad_requerida} "
                f"equipo(s), pero se proporcionaron {cantidad_equipos}."
            )

    return errors
