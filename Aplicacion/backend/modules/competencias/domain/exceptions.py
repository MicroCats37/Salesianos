"""Excepciones de dominio del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §10 ·
          `contract/api-wrapper-presenter-contract.md` §8

Cada excepción declara un `code` ESTABLE y de máquina. El texto que se
construye aquí es SOLO técnico (lo registra el log del servidor); la prosa
pública la decide el catálogo global `core/exceptions.py`.

Reglas del módulo:

- el rechazo de elegibilidad lleva un MOTIVO de máquina (`MotivoNoElegibilidad`)
  además del código: el backend publica la razón concreta y el cliente nunca
  la adivina (`QA-K01`);
- el conflicto de versión es SIEMPRE `RESOURCE_CHANGED` (409): el cliente
  recarga y reintenta, nunca aplica un cambio obsoleto en silencio
  (`frontend/05` §5);
- el motivo de una operación protegida es SIEMPRE obligatorio
  (`MOTIVO_REQUERIDO`, 422).
"""

from core.exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)


class CompetenciaNoEncontradaError(NotFoundError):
    """La competencia solicitada no existe (404)."""

    code = "COMPETENCIA_NO_ENCONTRADA"

    def __init__(self) -> None:
        super().__init__(resource="Competencia", code=self.code)


class CompetenciaEquipoNoEncontradaError(NotFoundError):
    """La participación del equipo en la competencia no existe (404)."""

    code = "COMPETENCIA_EQUIPO_NO_ENCONTRADA"

    def __init__(self) -> None:
        super().__init__(resource="Equipo de competencia", code=self.code)


class RondaNoEncontradaError(NotFoundError):
    """La ronda solicitada no existe (404)."""

    code = "RONDA_NO_ENCONTRADA"

    def __init__(self) -> None:
        super().__init__(resource="Ronda", code=self.code)


class EncuentroNoEncontradoError(NotFoundError):
    """El encuentro solicitado no existe (404)."""

    code = "ENCUENTRO_NO_ENCONTRADO"

    def __init__(self) -> None:
        super().__init__(resource="Encuentro", code=self.code)


class EquipoNoEncontradoError(NotFoundError):
    """El equipo de inscripción solicitado no existe (404).

    El código lo pidió DOM-02 al catálogo público (`A0-DOM02-03`): este módulo
    REUTILIZA el mismo código y no inventa otro para el mismo hecho.
    """

    code = "EQUIPO_NO_ENCONTRADO"

    def __init__(self) -> None:
        super().__init__(resource="Equipo", code=self.code)


class DisciplinaNoEncontradaError(NotFoundError):
    """La disciplina solicitada no existe en la edición (404)."""

    code = "DISCIPLINA_NO_ENCONTRADA"

    def __init__(self) -> None:
        super().__init__(resource="Disciplina", code=self.code)


class CategoriaNoEncontradaError(NotFoundError):
    """La categoría solicitada no existe en la edición (404).

    La CATEGORÍA es un hecho del DUEÑO (`modules.salesianos_fest`): este
    módulo sólo la REFERENCIA. Una categoría que no existe —o que es de otra
    edición— no se puede usar en una competencia, y el backend lo dice con su
    propio código.
    """

    code = "CATEGORIA_NO_ENCONTRADA"

    def __init__(self) -> None:
        super().__init__(resource="Categoría", code=self.code)


class CompetenciaDuplicadaError(ConflictError):
    """Ya existe una competencia con la misma identidad en la edición (409)."""

    code = "COMPETENCIA_DUPLICADA"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe una competencia con ese nombre en la edición y disciplina.",
            code=self.code,
        )


class CompetenciaEquipoDuplicadoError(ConflictError):
    """El equipo ya está incorporado a la competencia (409)."""

    code = "COMPETENCIA_EQUIPO_DUPLICADO"

    def __init__(self) -> None:
        super().__init__(
            "El equipo ya está incorporado a esta competencia.",
            code=self.code,
        )


class OrdenDuplicadoError(ConflictError):
    """El orden ya está ocupado por otra entrada activa (409)."""

    code = "ORDEN_DUPLICADO"

    def __init__(self) -> None:
        super().__init__("Ese orden ya está ocupado.", code=self.code)


class RondaDuplicadaError(ConflictError):
    """Ya existe una ronda con esa etiqueta o ese orden (409)."""

    code = "RONDA_DUPLICADA"

    def __init__(self) -> None:
        super().__init__("Ya existe una ronda con esa etiqueta o ese orden.", code=self.code)


class SolapamientoHorarioError(ConflictError):
    """El equipo ya juega en esa franja horaria (`RN-K03`) (409)."""

    code = "SOLAPAMIENTO_HORARIO"

    def __init__(self) -> None:
        super().__init__(
            "Uno de los equipos ya tiene un encuentro en esa franja horaria.",
            code=self.code,
        )


class HorarioInvalidoError(UnprocessableEntityError):
    """El horario no es un intervalo positivo del día de la competencia (422)."""

    code = "HORARIO_INVALIDO"

    def __init__(self) -> None:
        super().__init__(
            "El horario debe ser un intervalo positivo dentro del día de la competencia.",
            code=self.code,
        )


class VersionDesactualizadaError(ConflictError):
    """La versión que el cliente conoce ya no es la actual (`RESOURCE_CHANGED`)."""

    code = "RESOURCE_CHANGED"

    def __init__(self) -> None:
        super().__init__(
            "El recurso cambió mientras lo editabas.",
            code=self.code,
        )


class MotivoRequeridoError(UnprocessableEntityError):
    """La operación protegida exige un motivo auditado (422)."""

    code = "MOTIVO_REQUERIDO"

    def __init__(self) -> None:
        super().__init__(
            "La operación exige un motivo de entre 5 y 500 caracteres.",
            code=self.code,
        )


class TransicionInvalidaError(ConflictError):
    """El estado actual del encuentro no admite la operación (409)."""

    code = "TRANSICION_INVALIDA"

    def __init__(self) -> None:
        super().__init__(
            "El estado actual del encuentro no admite esta operación.",
            code=self.code,
        )


class GanadorInvalidoError(UnprocessableEntityError):
    """El ganador propuesto no ocupa ninguno de los dos slots (422)."""

    code = "GANADOR_INVALIDO"

    def __init__(self) -> None:
        super().__init__(
            "El ganador debe ser uno de los participantes del encuentro.",
            code=self.code,
        )


class EnlaceInvalidoError(UnprocessableEntityError):
    """El enlace al siguiente encuentro no es válido (422)."""

    code = "ENLACE_INVALIDO"

    def __init__(self) -> None:
        super().__init__(
            "El enlace al siguiente encuentro no es válido.",
            code=self.code,
        )


class SlotOcupadoError(ConflictError):
    """El slot de destino ya está ocupado por otro equipo (409)."""

    code = "SLOT_OCUPADO"

    def __init__(self) -> None:
        super().__init__("El slot de destino ya está ocupado.", code=self.code)


class DestinoBloqueadoError(ConflictError):
    """El destino ya transcurrió y la cascada NO puede aplicarse en silencio (409)."""

    code = "DESTINO_BLOQUEADO"

    def __init__(self) -> None:
        super().__init__(
            "El encuentro de destino ya transcurrió: la cascada requiere un "
            "override explícito y un motivo.",
            code=self.code,
        )


class ByeInvalidoError(UnprocessableEntityError):
    """Un bye manual exige EXACTAMENTE un equipo (422)."""

    code = "BYE_INVALIDO"

    def __init__(self) -> None:
        super().__init__(
            "Un bye manual requiere exactamente un equipo en el encuentro.",
            code=self.code,
        )


class ParticipanteInvalidoError(UnprocessableEntityError):
    """El participante propuesto no pertenece a la competencia (422)."""

    code = "PARTICIPANTE_INVALIDO"

    def __init__(self) -> None:
        super().__init__(
            "El participante no pertenece a esta competencia.",
            code=self.code,
        )


class EquipoNoElegibleError(UnprocessableEntityError):
    """El equipo no cumple la elegibilidad deportiva (`RN-K01`) (422).

    El MOTIVO (`MotivoNoElegibilidad`) viaja en `motivo` para que el
    backend pueda publicar la razón concreta sin construir prosa aquí.
    """

    code = "EQUIPO_NO_ELEGIBLE"

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(
            "El equipo no cumple los requisitos de elegibilidad.",
            code=self.code,
        )


__all__ = [
    "ByeInvalidoError",
    "CategoriaNoEncontradaError",
    "CompetenciaDuplicadaError",
    "CompetenciaEquipoDuplicadoError",
    "CompetenciaEquipoNoEncontradaError",
    "CompetenciaNoEncontradaError",
    "DestinoBloqueadoError",
    "DisciplinaNoEncontradaError",
    "EnlaceInvalidoError",
    "EncuentroNoEncontradoError",
    "EquipoNoElegibleError",
    "EquipoNoEncontradoError",
    "GanadorInvalidoError",
    "HorarioInvalidoError",
    "MotivoRequeridoError",
    "OrdenDuplicadoError",
    "ParticipanteInvalidoError",
    "RondaDuplicadaError",
    "RondaNoEncontradaError",
    "SlotOcupadoError",
    "SolapamientoHorarioError",
    "TransicionInvalidaError",
    "VersionDesactualizadaError",
]
