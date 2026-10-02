"""
Domain exceptions — specific exceptions for the inscripciones module.
"""
from core.exceptions import BusinessError, NotFoundError, ConflictError


class InscripcionNotFoundError(NotFoundError):
    """Raised when an Inscripcion is not found."""
    pass


class DisciplinaNotFoundError(NotFoundError):
    """Raised when a Disciplina is not found."""
    pass


class PaqueteNotFoundError(NotFoundError):
    """Raised when a Paquete is not found."""
    pass


class EventoNotFoundError(NotFoundError):
    """Raised when an Evento is not found."""
    pass


class EquipoNotFoundError(NotFoundError):
    """Raised when an EquipoInscrito is not found."""
    pass


class ParticipacionDuplicadaError(ConflictError):
    """Raised when a person is already registered in the same discipline and event (R11)."""
    pass


class CupoExcedidoError(BusinessError):
    """Raised when the package capacity is exceeded."""
    pass


class CupoEquipoError(BusinessError):
    """Raised when a team discipline capacity is exceeded."""
    pass


class ConsistenciaEquipoError(BusinessError):
    """Raised when there is an inconsistency between equipo and participacion."""
    pass


class DelegadoInelegibleError(BusinessError):
    """Raised when a delegate is not eligible (not responsible nor participant)."""
    pass


class DisciplinaNoEnPaqueteError(BusinessError):
    """Raised when a discipline is not part of the package."""
    pass


class CantidadDisciplinasInvalidaError(BusinessError):
    """Raised when the number of disciplines selected doesn't match package requirements."""
    pass


class MaxJugadoresExcedidoError(BusinessError):
    """Raised when adding a participant would exceed max_jugadores for the discipline."""
    pass


class EquipoDuplicadoError(ConflictError):
    """Raised when an equipo already exists for the same inscription+discipline (D7)."""
    pass


class PersonaNotFoundError(NotFoundError):
    """Raised when a persona_id is explicitly provided but the Persona does not exist."""

    def __init__(self, persona_id: str):
        super().__init__(
            resource="Persona",
            detail=f"ID {persona_id} no encontrado",
            code="PERSONA_NOT_FOUND",
        )


class ParticipanteInlineError(BusinessError):
    """Raised when inline participant data is invalid or processing fails."""

    def __init__(self, message: str, equipo_index: int | None = None, participante_index: int | None = None):
        detail_parts = []
        if equipo_index is not None:
            detail_parts.append(f"equipo[{equipo_index}]")
        if participante_index is not None:
            detail_parts.append(f"participante[{participante_index}]")
        prefix = f"[{' / '.join(detail_parts)}] " if detail_parts else ""
        super().__init__(message=prefix + message, code="PARTICIPANTE_INLINE_ERROR")
