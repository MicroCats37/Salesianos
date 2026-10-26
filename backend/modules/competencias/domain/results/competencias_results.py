"""
Result DTOs of the competencias module.

Internal objects returned by the orchestrators: the presenters of Phase 3
transform them into the HTTP schemas (contract/PLAN_REFACTORIZACION.md §3).
They are plain Pydantic models, never Django models.
"""
from datetime import date, datetime

from pydantic import BaseModel as PydanticBaseModel


class CompetenciaResult(PydanticBaseModel):
    """Public shape of a competition."""

    id: str
    evento_id: str
    disciplina_id: str
    categoria_id: str
    nombre: str
    fecha: date
    estado: str
    version: int
    created_at: datetime

    @classmethod
    def desde(cls, competencia) -> "CompetenciaResult":
        """Build the result from the model."""
        return cls(
            id=str(competencia.id),
            evento_id=str(competencia.evento_id),
            disciplina_id=str(competencia.disciplina_id),
            categoria_id=str(competencia.categoria_id),
            nombre=competencia.nombre,
            fecha=competencia.fecha,
            estado=competencia.estado,
            version=competencia.version,
            created_at=competencia.created_at,
        )


class CompetenciaListadoResult(CompetenciaResult):
    """Row of the list of competitions.

    It extends the result of the command with the three counters the read
    surface needs. They are computed by the selector with a CONSTANT number
    of queries, never re-derived by the client.
    """

    total_equipos: int = 0
    total_encuentros: int = 0
    total_encuentros_finalizados: int = 0


class CompetenciaEquipoResult(PydanticBaseModel):
    """Public shape of the participation of a team in the bracket."""

    id: str
    competencia_id: str
    equipo_id: str
    equipo_nombre: str = ""
    orden: int
    estado: str
    version: int
    created_at: datetime

    @classmethod
    def desde(cls, entrada) -> "CompetenciaEquipoResult":
        """Build the result from the model."""
        return cls(
            id=str(entrada.id),
            competencia_id=str(entrada.competencia_id),
            equipo_id=str(entrada.equipo_id),
            equipo_nombre=getattr(
                getattr(entrada, "equipo", None), "nombre", ""
            )
            or "",
            orden=entrada.orden,
            estado=entrada.estado,
            version=entrada.version,
            created_at=entrada.created_at,
        )


class RondaResult(PydanticBaseModel):
    """Public shape of a round of the bracket."""

    id: str
    competencia_id: str
    etiqueta: str
    orden: int
    estado: str
    version: int
    total_encuentros: int = 0
    created_at: datetime

    @classmethod
    def desde(cls, ronda) -> "RondaResult":
        """Build the result from the model."""
        return cls(
            id=str(ronda.id),
            competencia_id=str(ronda.competencia_id),
            etiqueta=ronda.etiqueta,
            orden=ronda.orden,
            estado=ronda.estado,
            version=ronda.version,
            created_at=ronda.created_at,
        )


class EncuentroResult(PydanticBaseModel):
    """Public shape of an encounter of the bracket.

    The result carries BOTH the data of the command and the data the read
    surface needs (the names of the teams and the round they belong to). The
    extra fields are optional so the result of a command never breaks.
    """

    id: str
    ronda_id: str
    orden: int
    participante_1_id: str | None = None
    participante_2_id: str | None = None
    inicio_programado: datetime | None = None
    fin_programado: datetime | None = None
    estado: str
    estado_pre_suspension: str | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    es_bye: bool
    ganador_id: str | None = None
    puntaje_1: int | None = None
    puntaje_2: int | None = None
    marcador_detalle: str = ""
    siguiente_encuentro_id: str | None = None
    slot_destino: str | None = None
    ganador_propagado_id: str | None = None
    version: int
    created_at: datetime
    # ── read surface (optional) ────────────────────────────────────────────
    competencia_id: str | None = None
    competencia_nombre: str | None = None
    ronda_etiqueta: str | None = None
    ronda_orden: int | None = None
    participante_1_nombre: str | None = None
    participante_2_nombre: str | None = None

    @classmethod
    def desde(cls, encuentro) -> "EncuentroResult":
        """Build the result from the model."""
        return cls(
            id=str(encuentro.id),
            ronda_id=str(encuentro.ronda_id),
            orden=encuentro.orden,
            participante_1_id=(
                str(encuentro.participante_1_id)
                if encuentro.participante_1_id
                else None
            ),
            participante_2_id=(
                str(encuentro.participante_2_id)
                if encuentro.participante_2_id
                else None
            ),
            inicio_programado=encuentro.inicio_programado,
            fin_programado=encuentro.fin_programado,
            estado=encuentro.estado,
            estado_pre_suspension=encuentro.estado_pre_suspension,
            iniciado_en=encuentro.iniciado_en,
            finalizado_en=encuentro.finalizado_en,
            es_bye=encuentro.es_bye,
            ganador_id=(
                str(encuentro.ganador_id) if encuentro.ganador_id else None
            ),
            puntaje_1=encuentro.puntaje_1,
            puntaje_2=encuentro.puntaje_2,
            marcador_detalle=encuentro.marcador_detalle or "",
            siguiente_encuentro_id=(
                str(encuentro.siguiente_encuentro_id)
                if encuentro.siguiente_encuentro_id
                else None
            ),
            slot_destino=encuentro.slot_destino,
            ganador_propagado_id=(
                str(encuentro.ganador_propagado_id)
                if encuentro.ganador_propagado_id
                else None
            ),
            version=encuentro.version,
            created_at=encuentro.created_at,
            competencia_id=_competencia_id_de(encuentro),
            competencia_nombre=_competencia_nombre_de(encuentro),
            ronda_etiqueta=_ronda_etiqueta_de(encuentro),
            ronda_orden=_ronda_orden_de(encuentro),
            participante_1_nombre=_equipo_nombre_de(encuentro, "participante_1"),
            participante_2_nombre=_equipo_nombre_de(encuentro, "participante_2"),
        )


class CompetenciaDetalleResult(CompetenciaListadoResult):
    """Detail of a competition: its teams and its rounds."""

    equipos: list[CompetenciaEquipoResult] = []
    rondas: list[RondaResult] = []


class RondaCuadroResult(PydanticBaseModel):
    """Column of the bracket: a round and its encounters."""

    id: str
    etiqueta: str
    orden: int
    estado: str
    encuentros: list[EncuentroResult] = []


class CuadroResult(PydanticBaseModel):
    """Bracket of a competition.

    An EMPTY or PARTIAL bracket is a valid bracket: the rounds and the
    encounters that exist are returned as they are, and NOTHING is invented
    (spec: "un cuadro vacío o parcial MUST ser legible y editable sin
    inventar participantes ni avances").
    """

    competencia_id: str
    nombre: str
    fecha: date
    estado: str
    total_equipos: int = 0
    rondas: list[RondaCuadroResult] = []


class AgendaResult(PydanticBaseModel):
    """Agenda of ONE day: the encounters scheduled that day."""

    fecha: date
    total: int = 0
    encuentros: list[EncuentroResult] = []


# ── helpers of the read surface ───────────────────────────────────────────────


def _competencia_id_de(encuentro) -> str | None:
    """Return the id of the competition of the encounter (if it is loaded)."""
    ronda = getattr(encuentro, "ronda", None)
    competencia_id = getattr(ronda, "competencia_id", None)
    return str(competencia_id) if competencia_id else None


def _competencia_nombre_de(encuentro) -> str | None:
    """Return the name of the competition of the encounter (if it is loaded)."""
    ronda = getattr(encuentro, "ronda", None)
    competencia = getattr(ronda, "competencia", None)
    return getattr(competencia, "nombre", None)


def _ronda_etiqueta_de(encuentro) -> str | None:
    """Return the label of the round of the encounter (if it is loaded)."""
    return getattr(getattr(encuentro, "ronda", None), "etiqueta", None)


def _ronda_orden_de(encuentro) -> int | None:
    """Return the order of the round of the encounter (if it is loaded)."""
    return getattr(getattr(encuentro, "ronda", None), "orden", None)


def _equipo_nombre_de(encuentro, slot: str) -> str | None:
    """Return the name of the team that occupies one of the two slots."""
    participante = getattr(encuentro, slot, None)
    if participante is None:
        return None
    return getattr(getattr(participante, "equipo", None), "nombre", None)


class AvancePreviewResult(PydanticBaseModel):
    """Proposal of the propagation of the winner to the next encounter.

    The preview NEVER writes: it is the proposal the administrator confirms
    (design: "el sistema MUST proponer su colocación en un slot enlazado
    del siguiente encuentro y requerir confirmación administrativa
    idempotente").
    """

    encuentro_id: str
    siguiente_encuentro_id: str
    slot_destino: str
    ganador_id: str
    ocupante_actual_id: str | None = None
    ya_propagado: bool = False
    bloqueado: bool = False
    motivo_bloqueo: str | None = None


class AvanceResult(PydanticBaseModel):
    """Outcome of the propagation of the winner."""

    encuentro_origen_id: str
    siguiente_encuentro_id: str
    slot_destino: str
    ganador_id: str
    ya_aplicado: bool = False
    destino: EncuentroResult


class ImpactoDescendienteResult(PydanticBaseModel):
    """Impact of a correction over ONE descendant of the link.

    A descendant is BLOCKED when it already started (`iniciado_en`), when it
    finished or when it was cancelled: rewriting it requires an explicit
    override with an accepted impact.
    """

    encuentro_id: str
    slot: str
    estado: str
    ocupante_actual_id: str | None = None
    ganador_propagado_id: str | None = None
    bloqueado: bool = False
    motivo_bloqueo: str | None = None
    se_reemplaza: bool = False
    se_limpia_resultado: bool = False


class CorreccionPreviewResult(PydanticBaseModel):
    """Impact analysis of the correction of the winner of an encounter."""

    encuentro_id: str
    ganador_actual_id: str | None = None
    ganador_nuevo_id: str
    requiere_override: bool = False
    descendientes: list[ImpactoDescendienteResult] = []


class CorreccionResult(PydanticBaseModel):
    """Outcome of the correction of the winner of an encounter."""

    encuentro_id: str
    ganador_id: str
    requirio_override: bool = False
    descendientes_afectados: int = 0
    encuentro: EncuentroResult
    descendientes: list[ImpactoDescendienteResult] = []
