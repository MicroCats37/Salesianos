"""DTOs de SALIDA del módulo `competencias` (result objects).

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 ·
          `contract/api-wrapper-presenter-contract.md` §3

Los `results/` son la SALIDA de los servicios y de los selectores: son
objetos de dominio TIPADOS, nunca modelos de Django y nunca esquemas HTTP.
El presenter los proyecta a los wrappers de `presentation/schemas/`.

**La fuente operativa es UNA.** `frontend/05` §1 y `FL-11` paso 6 exigen que
la agenda, el cuadro y el detalle del encuentro se deriven de la MISMA
fuente. Por eso estos results tienen UNA forma canónica de encuentro
(`EncuentroResult`) y las tres superficies la reutilizan: la agenda no
inventa su propio tipo de encuentro.

**Lo que NO viaja aquí:** el `detalle` técnico de la auditoría (nunca se
publica), el SQL, los identificadores internos del proveedor y cualquier
prosa técnica. Los identificadores que sí viajan son los UUID de negocio
(`competencia`, `ronda`, `encuentro`, `equipo`): son parte del contrato
público del recurso, no un dato interno.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class CompetenciaEquipoResult(BaseModel):
    """La participación de un equipo en el cuadro."""

    id: str = Field(..., description="Identificador de la participación.")
    equipo_id: str = Field(..., description="Identificador del equipo de inscripción.")
    equipo_nombre: str = Field(..., description="Nombre del equipo de inscripción.")
    orden: int = Field(..., description="Semilla manual del equipo en el cuadro.")
    estado: str = Field(..., description="`ACTIVO` o `RETIRADO`.")
    version: int = Field(..., description="Versión del bloqueo optimista.")


class ParticipanteResult(BaseModel):
    """Un SLOT del encuentro, con la identidad del equipo que lo ocupa."""

    slot: str = Field(..., description="`PARTICIPANTE_1` o `PARTICIPANTE_2`.")
    competencia_equipo_id: str | None = Field(
        default=None,
        description="Participación que ocupa el slot. Vacío si el slot está libre.",
    )
    equipo_id: str | None = Field(default=None, description="Equipo de inscripción.")
    equipo_nombre: str | None = Field(default=None, description="Nombre del equipo.")
    orden: int | None = Field(default=None, description="Semilla del equipo en el cuadro.")


class EncuentroResult(BaseModel):
    """La forma canónica de un encuentro.

    Es la MISMA forma que consumen la agenda, el cuadro y el detalle: no hay
    tres wrappers distintos para el mismo dato (`FL-11` paso 6).
    """

    id: str = Field(..., description="Identificador del encuentro.")
    ronda_id: str = Field(..., description="Ronda del encuentro.")
    ronda_etiqueta: str = Field(..., description="Etiqueta de la ronda.")
    ronda_orden: int = Field(..., description="Orden de la ronda en el cuadro.")
    competencia_id: str = Field(..., description="Competencia del encuentro.")
    orden: int = Field(..., description="Orden del encuentro dentro de su ronda.")
    estado: str = Field(..., description="Estado operativo del encuentro.")
    es_bye: bool = Field(..., description="Si el encuentro es un pase libre manual.")
    participantes: list[ParticipanteResult] = Field(
        default_factory=list,
        description="Los dos slots, en orden.",
    )
    inicio_programado: datetime | None = Field(
        default=None,
        description="Inicio programado del encuentro.",
    )
    fin_programado: datetime | None = Field(
        default=None,
        description="Fin programado del encuentro.",
    )
    puntaje_1: int | None = Field(default=None, description="Puntaje del slot 1.")
    puntaje_2: int | None = Field(default=None, description="Puntaje del slot 2.")
    marcador_detalle: str = Field(default="", description="Detalle informativo del marcador.")
    ganador_equipo_id: str | None = Field(
        default=None,
        description="Equipo ganador. Es autoritativo: ocupa uno de los slots.",
    )
    ganador_equipo_nombre: str | None = Field(default=None, description="Nombre del ganador.")
    siguiente_encuentro_id: str | None = Field(
        default=None,
        description="Encuentro al que avanza el ganador.",
    )
    slot_destino: str | None = Field(
        default=None,
        description="Slot del encuentro de destino que recibe al ganador.",
    )
    iniciado_en: datetime | None = Field(default=None, description="Momento de inicio.")
    finalizado_en: datetime | None = Field(default=None, description="Momento de fin.")
    version: int = Field(..., description="Versión del bloqueo optimista.")
    acciones: list[str] = Field(
        default_factory=list,
        description=(
            "Acciones que el backend ADMITE en el estado actual del encuentro. "
            "La interfaz las usa para ocultar lo imposible, pero la "
            "autorización definitiva es del backend (`RN-A01`)."
        ),
    )


class RondaResult(BaseModel):
    """Una ronda del cuadro, con sus encuentros."""

    id: str = Field(..., description="Identificador de la ronda.")
    etiqueta: str = Field(..., description="Etiqueta de la ronda.")
    orden: int = Field(..., description="Orden de la ronda en el cuadro.")
    estado: str = Field(..., description="`ACTIVA` o `INVALIDADA`.")
    version: int = Field(..., description="Versión del bloqueo optimista.")
    encuentros: list[EncuentroResult] = Field(
        default_factory=list,
        description="Encuentros de la ronda, en orden.",
    )


class CompetenciaDetalleResult(BaseModel):
    """El detalle operativo de una competencia.

    Es la fuente ÚNICA de la agenda, del cuadro y del detalle: las tres
    superficies leen estos mismos datos.
    """

    id: str = Field(..., description="Identificador de la competencia.")
    edicion_id: str = Field(..., description="Edición de la competencia.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    nombre: str = Field(..., description="Nombre del torneo.")
    estado: str = Field(..., description="Estado del torneo.")
    fecha: date = Field(..., description="Día de la competencia.")
    version: int = Field(..., description="Versión del bloqueo optimista.")
    equipos: list[CompetenciaEquipoResult] = Field(
        default_factory=list,
        description="Equipos del cuadro.",
    )
    rondas: list[RondaResult] = Field(
        default_factory=list,
        description="Rondas del cuadro, en orden.",
    )


class CompetenciaListadoResult(BaseModel):
    """La fila de la lista de competencias de la edición.

    Los tres contadores los calcula el SELECTOR con un número constante de
    consultas: el cliente nunca los re-deriva (`RN-A02`).
    """

    id: str = Field(..., description="Identificador de la competencia.")
    edicion_id: str = Field(..., description="Edición de la competencia.")
    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    nombre: str = Field(..., description="Nombre del torneo.")
    estado: str = Field(..., description="Estado del torneo.")
    fecha: date = Field(..., description="Día de la competencia.")
    total_equipos: int = Field(default=0, description="Equipos activos del cuadro.")
    total_encuentros: int = Field(default=0, description="Encuentros del cuadro.")
    total_encuentros_finalizados: int = Field(
        default=0,
        description="Encuentros finalizados.",
    )


class AgendaResult(BaseModel):
    """La agenda transversal del día, en el alcance de la edición."""

    edicion_id: str = Field(..., description="Edición de la agenda.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    fecha: date = Field(..., description="Día de la agenda.")
    total: int = Field(default=0, description="Encuentros programados del día.")
    encuentros: list[EncuentroResult] = Field(
        default_factory=list,
        description="Encuentros del día, ordenados por hora de inicio.",
    )


class ResultadoRegistradoResult(BaseModel):
    """El resultado autoritativo de un encuentro ya registrado."""

    encuentro: EncuentroResult = Field(..., description="El encuentro ya finalizado.")
    ganador_equipo_id: str = Field(..., description="Equipo ganador.")
    ganador_equipo_nombre: str = Field(..., description="Nombre del equipo ganador.")


class AvancePreviewResult(BaseModel):
    """La VISTA PREVIA del avance. NUNCA escribe.

    `QA-K04`: la previa informa del efecto exacto (destino, slot, ganador,
    ocupante actual) y de si la cascada está bloqueada.
    """

    encuentro_id: str = Field(..., description="Encuentro de origen.")
    siguiente_encuentro_id: str = Field(..., description="Encuentro de destino.")
    slot_destino: str = Field(..., description="Slot del destino que recibe al ganador.")
    ganador_equipo_id: str = Field(..., description="Equipo que avanzaría.")
    ganador_equipo_nombre: str = Field(..., description="Nombre del equipo que avanzaría.")
    ocupante_actual_equipo_id: str | None = Field(
        default=None,
        description="Equipo que ocupa hoy ese slot, si lo hay.",
    )
    ya_propagado: bool = Field(
        default=False,
        description="Si el avance ya está aplicado (reintento idempotente).",
    )
    bloqueado: bool = Field(
        default=False,
        description="Si el destino ya transcurrió y la cascada no puede aplicarse.",
    )
    motivo_bloqueo: str | None = Field(
        default=None,
        description="Explicación del bloqueo, en prosa de negocio.",
    )
    puede_confirmar: bool = Field(
        default=False,
        description="Si el backend admite confirmar el avance ahora.",
    )


class AvanceResult(BaseModel):
    """El avance CONFIRMADO."""

    encuentro_origen_id: str = Field(..., description="Encuentro de origen.")
    siguiente_encuentro_id: str = Field(..., description="Encuentro de destino.")
    slot_destino: str = Field(..., description="Slot del destino que recibió al ganador.")
    ganador_equipo_id: str = Field(..., description="Equipo propagado.")
    ganador_equipo_nombre: str = Field(..., description="Nombre del equipo propagado.")
    ya_aplicado: bool = Field(
        default=False,
        description="Si el avance ya estaba aplicado (reintento idempotente).",
    )
    destino: EncuentroResult = Field(..., description="El destino ya actualizado.")


class CorreccionImpactoResult(BaseModel):
    """El impacto de la corrección sobre UN descendiente.

    `QA-K03`: el impacto es EXPLÍCITO. Cada descendiente dice qué le pasa:
    se reemplaza su occupant, se vacía su slot, se anula su resultado, o no
    se le toca.
    """

    encuentro_id: str = Field(..., description="Encuentro descendiente.")
    slot: str = Field(..., description="Slot afectado del descendiente.")
    bloqueado: bool = Field(
        default=False,
        description="Si el descendiente ya transcurrió y no puede reescribirse.",
    )
    motivo_bloqueo: str | None = Field(
        default=None,
        description="Explicación del bloqueo, en prosa de negocio.",
    )
    reemplaza: bool = Field(default=False, description="Si se sustituye el valor propagado.")
    limpia_slot: bool = Field(default=False, description="Si se vacía el slot del descendiente.")
    limpia_resultado: bool = Field(
        default=False,
        description="Si se anula el resultado derivado del descendiente.",
    )
    afecta: bool = Field(default=False, description="Si el descendiente cambia de verdad.")


class CorreccionPreviewResult(BaseModel):
    """La VISTA PREVIA de la corrección. NUNCA escribe."""

    encuentro_id: str = Field(..., description="Encuentro corregido.")
    ganador_actual_equipo_id: str | None = Field(
        default=None,
        description="Equipo ganador actual, si lo hay.",
    )
    ganador_nuevo_equipo_id: str = Field(..., description="Equipo ganador propuesto.")
    ganador_nuevo_equipo_nombre: str = Field(..., description="Nombre del ganador propuesto.")
    requiere_override: bool = Field(
        default=False,
        description=(
            "Si algún descendiente ya transcurrió: la cascada NO puede "
            "aplicarse en silencio (`RN-K02`)."
        ),
    )
    total_afectados: int = Field(
        default=0,
        description="Cuántos descendientes cambian de verdad.",
    )
    descendientes: list[CorreccionImpactoResult] = Field(
        default_factory=list,
        description="Impacto sobre cada descendiente de la cadena.",
    )
    puede_confirmar: bool = Field(
        default=False,
        description="Si el backend admite la corrección ahora.",
    )


class CorreccionResult(BaseModel):
    """La corrección APLICADA."""

    encuentro_id: str = Field(..., description="Encuentro corregido.")
    ganador_nuevo_equipo_id: str = Field(..., description="Equipo ganador nuevo.")
    ganador_nuevo_equipo_nombre: str = Field(..., description="Nombre del ganador nuevo.")
    descendientes_afectados: int = Field(
        default=0,
        description="Cuántos descendientes cambiaron de verdad.",
    )
    override_aplicado: bool = Field(
        default=False,
        description="Si la cascada se aplicó con autorización explícita.",
    )
    encuentro: EncuentroResult = Field(..., description="El encuentro corregido.")
    descendientes: list[CorreccionImpactoResult] = Field(
        default_factory=list,
        description="Impacto aplicado sobre cada descendiente.",
    )


class OperacionAuditadaResult(BaseModel):
    """El ACTA de una operación protegida.

    El `detalle` técnico (antes/después) NUNCA se publica: el acta pública
    lleva la acción, el motivo y el momento.
    """

    id: str = Field(..., description="Identificador del acta.")
    accion: str = Field(..., description="Acción auditada.")
    actor_id: str | None = Field(default=None, description="Cuenta que la ejecutó.")
    motivo: str = Field(..., description="Motivo auditado de la operación.")
    created_at: datetime = Field(..., description="Momento de la operación.")


__all__ = [
    "AgendaResult",
    "AvancePreviewResult",
    "AvanceResult",
    "CompetenciaEquipoResult",
    "CompetenciaListadoResult",
    "CompetenciaDetalleResult",
    "CorreccionImpactoResult",
    "CorreccionPreviewResult",
    "CorreccionResult",
    "EncuentroResult",
    "OperacionAuditadaResult",
    "ParticipanteResult",
    "ResultadoRegistradoResult",
    "RondaResult",
]
