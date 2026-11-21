"""Esquemas HTTP del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.7 ·
          `contract/api-wrapper-presenter-contract.md` §2, §7

**UNA forma de encuentro.** La agenda, el cuadro y el detalle del encuentro
comparten el MISMO wrapper `EncuentroOut`: no hay tres formas de proyección
para el mismo dato (`FL-11` paso 6). El espejo Zod del frontend replica
exactamente estos campos.

**El `expected_version` viaja en el payload de las escrituras.** Es la
protección de concurrencia que el contrato pide (`frontend/05` §5): el
cliente envía la versión que conoce y el servidor la compara antes de
escribir.

**Los motivos de rechazo** viajan como CÓDIGO (`MotivoNoElegibilidad`), no
como prosa: el backend publica la razón y el cliente nunca la adivina
(`QA-K01`).

**La CATEGORÍA es parte de la identidad del torneo**: el alta la exige
(`categoria_id`) y las salidas la publican (`categoria_id` +
`categoria_nombre`), con el MISMO patrón que la disciplina.
"""

from datetime import date, datetime

from ninja import Schema
from pydantic import Field


# ── Salidas ──────────────────────────────────────────────────────────────────


class ParticipanteOut(Schema):
    """Un slot del encuentro."""

    slot: str = Field(..., description="`PARTICIPANTE_1` o `PARTICIPANTE_2`.")
    competencia_equipo_id: str | None = Field(
        default=None,
        description="Participación que ocupa el slot. Vacío si el slot está libre.",
    )
    equipo_id: str | None = Field(default=None, description="Equipo de inscripción.")
    equipo_nombre: str | None = Field(default=None, description="Nombre del equipo.")
    orden: int | None = Field(default=None, description="Semilla del equipo en el cuadro.")


class EncuentroOut(Schema):
    """La forma canónica de un encuentro en las TRES superficies."""

    id: str = Field(..., description="Identificador del encuentro.")
    ronda_id: str = Field(..., description="Ronda del encuentro.")
    ronda_etiqueta: str = Field(..., description="Etiqueta de la ronda.")
    ronda_orden: int = Field(..., description="Orden de la ronda en el cuadro.")
    competencia_id: str = Field(..., description="Competencia del encuentro.")
    orden: int = Field(..., description="Orden del encuentro dentro de su ronda.")
    estado: str = Field(..., description="Estado operativo del encuentro.")
    es_bye: bool = Field(..., description="Si el encuentro es un pase libre manual.")
    participantes: list[ParticipanteOut] = Field(
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
        description="Acciones que el backend admite en el estado actual.",
    )


class RondaOut(Schema):
    """Una ronda del cuadro con sus encuentros."""

    id: str = Field(..., description="Identificador de la ronda.")
    etiqueta: str = Field(..., description="Etiqueta de la ronda.")
    orden: int = Field(..., description="Orden de la ronda en el cuadro.")
    estado: str = Field(..., description="`ACTIVA` o `INVALIDADA`.")
    version: int = Field(..., description="Versión del bloqueo optimista.")
    encuentros: list[EncuentroOut] = Field(
        default_factory=list,
        description="Encuentros de la ronda, en orden.",
    )


class EncuentroPublicoOut(Schema):
    """El encuentro en su forma PÚBLICA.

    Es la MISMA proyección canónica que la agenda, el cuadro y el detalle
    (`EncuentroResult`), con DOS diferencias deliberadas: el estado que se
    publica es el PÚBLICO —no el del flujo administrativo— y no viaja ninguna
    acción de administración. La superficie pública es de SOLO LECTURA: no
    ofrece operaciones.

    **El ganador es la autoridad.** `puntaje_1`/`puntaje_2` son
    INFORMATIVOS: el backend nunca deduce el ganador del marcador y el
    cliente tampoco (`explore` §9).
    """

    id: str = Field(..., description="Identificador del encuentro.")
    ronda_id: str = Field(..., description="Ronda del encuentro.")
    ronda_etiqueta: str = Field(..., description="Etiqueta de la ronda.")
    ronda_orden: int = Field(..., description="Orden de la ronda en el cuadro.")
    competencia_id: str = Field(..., description="Competencia del encuentro.")
    orden: int = Field(..., description="Orden del encuentro dentro de su ronda.")
    estado_publico: str = Field(
        ...,
        description="`PROGRAMA`, `EN_VIVO` o `FINALIZADO`.",
    )
    es_bye: bool = Field(..., description="Si el encuentro es un pase libre manual.")
    participantes: list[ParticipanteOut] = Field(
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
    iniciado_en: datetime | None = Field(default=None, description="Momento de inicio.")
    finalizado_en: datetime | None = Field(default=None, description="Momento de fin.")
    puntaje_1: int | None = Field(
        default=None,
        description="Puntaje del slot 1. Es INFORMATIVO: no decide el ganador.",
    )
    puntaje_2: int | None = Field(
        default=None,
        description="Puntaje del slot 2. Es INFORMATIVO: no decide el ganador.",
    )
    marcador_detalle: str = Field(default="", description="Detalle informativo del marcador.")
    ganador_equipo_id: str | None = Field(
        default=None,
        description="Equipo ganador. Es la AUTORIDAD de la progresión.",
    )
    ganador_equipo_nombre: str | None = Field(default=None, description="Nombre del ganador.")
    version: int = Field(..., description="Versión del bloqueo optimista.")


class EncuentrosPublicosOut(Schema):
    """Los encuentros publicables de la edición, en sus TRES cubos.

    Los cubos son la presentación que consume el público: lo que está en
    juego, lo que viene y lo que ya terminó. Los tres son disjuntos y su
    unión es TODA la superficie pública de la edición.
    """

    edicion_id: str = Field(..., description="Edición de la que se publica.")
    edicion_nombre: str = Field(default="", description="Nombre de la edición.")
    total: int = Field(
        default=0,
        description="Encuentros publicables de la edición, en los tres cubos.",
    )
    en_vivo: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Encuentros en juego.",
    )
    proximos: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Encuentros del programa, los más próximos primero.",
    )
    finalizados: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Encuentros con resultado, los más recientes primero.",
    )


class CompetenciaEquipoOut(Schema):
    """La participación de un equipo en el cuadro."""

    id: str = Field(..., description="Identificador de la participación.")
    equipo_id: str = Field(..., description="Identificador del equipo de inscripción.")
    equipo_nombre: str = Field(..., description="Nombre del equipo de inscripción.")
    orden: int = Field(..., description="Semilla manual del equipo en el cuadro.")
    estado: str = Field(..., description="`ACTIVO` o `RETIRADO`.")
    version: int = Field(..., description="Versión del bloqueo optimista.")


class MisPartidosOut(Schema):
    """Los partidos de la CUENTA, en sus tres cubos.

    Es la lectura autenticada de "MIS PARTIDOS": la identidad la resuelve el
    servidor y el cliente no envía ninguna persona, usuario ni equipo.

    El encuentro es el MISMO que publica la superficie pública —los equipos,
    el marcador, el ganador explícito y la versión— porque la cuenta necesita
    exactamente esos datos y ninguno de las afordancias de administración.
    """

    edicion_id: str = Field(default="", description="Edición de los partidos.")
    edicion_nombre: str = Field(default="", description="Nombre de la edición.")
    total: int = Field(default=0, description="Partidos de la cuenta.")
    equipos: list[CompetenciaEquipoOut] = Field(
        default_factory=list,
        description="Los equipos de la cuenta en el cuadro.",
    )
    en_vivo: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Los partidos que se están jugando.",
    )
    proximos: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Los partidos del programa, los más próximos primero.",
    )
    finalizados: list[EncuentroPublicoOut] = Field(
        default_factory=list,
        description="Los partidos con resultado, los más recientes primero.",
    )


class CompetenciaListadoOut(Schema):
    """La fila de la lista de competencias de la edición."""

    id: str = Field(..., description="Identificador de la competencia.")
    edicion_id: str = Field(..., description="Edición de la competencia.")
    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    categoria_id: str = Field(..., description="Categoría del torneo.")
    categoria_nombre: str = Field(..., description="Nombre de la categoría.")
    nombre: str = Field(..., description="Nombre del torneo.")
    estado: str = Field(..., description="Estado del torneo.")
    fecha: date = Field(..., description="Día de la competencia.")
    total_equipos: int = Field(default=0, description="Equipos activos del cuadro.")
    total_encuentros: int = Field(default=0, description="Encuentros del cuadro.")
    total_encuentros_finalizados: int = Field(
        default=0,
        description="Encuentros finalizados.",
    )


class CompetenciaDetalleOut(Schema):
    """El detalle operativo de una competencia."""

    id: str = Field(..., description="Identificador de la competencia.")
    edicion_id: str = Field(..., description="Edición de la competencia.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    categoria_id: str = Field(..., description="Categoría del torneo.")
    categoria_nombre: str = Field(..., description="Nombre de la categoría.")
    nombre: str = Field(..., description="Nombre del torneo.")
    estado: str = Field(..., description="Estado del torneo.")
    fecha: date = Field(..., description="Día de la competencia.")
    version: int = Field(..., description="Versión del bloqueo optimista.")
    equipos: list[CompetenciaEquipoOut] = Field(
        default_factory=list,
        description="Equipos del cuadro.",
    )
    rondas: list[RondaOut] = Field(
        default_factory=list,
        description="Rondas del cuadro, en orden.",
    )


class AgendaOut(Schema):
    """La agenda transversal del día."""

    edicion_id: str = Field(..., description="Edición de la agenda.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    fecha: date = Field(..., description="Día de la agenda.")
    total: int = Field(default=0, description="Encuentros programados del día.")
    encuentros: list[EncuentroOut] = Field(
        default_factory=list,
        description="Encuentros del día, ordenados por hora de inicio.",
    )


class EquipoElegibleOut(Schema):
    """El veredicto de elegibilidad de un equipo candidato."""

    equipo_id: str = Field(..., description="Equipo de inscripción evaluado.")
    nombre: str = Field(..., description="Nombre del equipo.")
    edicion_id: str = Field(..., description="Edición a la que pertenece el equipo.")
    disciplina_id: str = Field(..., description="Disciplina del equipo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    categoria_id: str | None = Field(
        default=None,
        description="Categoría del equipo. Vacía si el equipo no tiene categoría asignada.",
    )
    categoria_nombre: str = Field(
        default="",
        description="Nombre de la categoría del equipo.",
    )
    estado: str = Field(..., description="Estado del equipo en su inscripción.")
    es_elegible: bool = Field(..., description="Si el equipo puede competir.")
    motivo: str = Field(
        ...,
        description="Código de `MotivoNoElegibilidad` con la razón del veredicto.",
    )
    participantes_activos: int = Field(
        ...,
        description="Participantes activos del equipo en el pool.",
    )
    minimo_requerido: int = Field(
        ...,
        description="Mínimo de participantes que exige la disciplina.",
    )


class ResultadoRegistradoOut(Schema):
    """El resultado autoritativo ya registrado."""

    encuentro: EncuentroOut = Field(..., description="El encuentro ya finalizado.")
    ganador_equipo_id: str = Field(..., description="Equipo ganador.")
    ganador_equipo_nombre: str = Field(..., description="Nombre del equipo ganador.")


class AvancePreviewOut(Schema):
    """La vista previa del avance. NO escribe."""

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
        description="Si el avance ya está aplicado.",
    )
    bloqueado: bool = Field(
        default=False,
        description="Si el destino ya transcurrió.",
    )
    motivo_bloqueo: str | None = Field(
        default=None,
        description="Explicación del bloqueo, en prosa de negocio.",
    )
    puede_confirmar: bool = Field(
        default=False,
        description="Si el backend admite confirmar el avance ahora.",
    )


class AvanceOut(Schema):
    """El avance confirmado."""

    encuentro_origen_id: str = Field(..., description="Encuentro de origen.")
    siguiente_encuentro_id: str = Field(
        ...,
        description="Encuentro de destino.",
    )
    slot_destino: str = Field(..., description="Slot del destino que recibió al ganador.")
    ganador_equipo_id: str = Field(..., description="Equipo propagado.")
    ganador_equipo_nombre: str = Field(..., description="Nombre del equipo propagado.")
    ya_aplicado: bool = Field(
        default=False,
        description="Si el avance ya estaba aplicado.",
    )
    destino: EncuentroOut = Field(..., description="El destino ya actualizado.")


class CorreccionImpactoOut(Schema):
    """El impacto de la corrección sobre un descendiente."""

    encuentro_id: str = Field(..., description="Encuentro descendiente.")
    slot: str = Field(..., description="Slot afectado del descendiente.")
    bloqueado: bool = Field(
        default=False,
        description="Si el descendiente ya transcurrió.",
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


class CorreccionPreviewOut(Schema):
    """La vista previa de la corrección. NO escribe."""

    encuentro_id: str = Field(..., description="Encuentro corregido.")
    ganador_actual_equipo_id: str | None = Field(
        default=None,
        description="Equipo ganador actual, si lo hay.",
    )
    ganador_nuevo_equipo_id: str = Field(..., description="Equipo ganador propuesto.")
    ganador_nuevo_equipo_nombre: str = Field(..., description="Nombre del ganador propuesto.")
    requiere_override: bool = Field(
        default=False,
        description="Si algún descendiente ya transcurrió.",
    )
    total_afectados: int = Field(
        default=0,
        description="Cuántos descendientes cambian de verdad.",
    )
    descendientes: list[CorreccionImpactoOut] = Field(
        default_factory=list,
        description="Impacto sobre cada descendiente de la cadena.",
    )
    puede_confirmar: bool = Field(
        default=False,
        description="Si el backend admite la corrección ahora.",
    )


class CorreccionOut(Schema):
    """La corrección aplicada."""

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
    encuentro: EncuentroOut = Field(..., description="El encuentro corregido.")
    descendientes: list[CorreccionImpactoOut] = Field(
        default_factory=list,
        description="Impacto aplicado sobre cada descendiente.",
    )


# ── Entradas ─────────────────────────────────────────────────────────────────


class CompetenciaCrearIn(Schema):
    """Alta de una competencia."""

    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    categoria_id: str = Field(
        ...,
        description=(
            "Categoría del torneo. Es OBLIGATORIA: la identidad de una "
            "competencia es (edición, disciplina, categoría, nombre)."
        ),
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del torneo.",
    )
    fecha: date = Field(..., description="Día de la competencia.")


class EquipoIncorporarIn(Schema):
    """Incorporación de un equipo al cuadro."""

    equipo_id: str = Field(..., description="Equipo de inscripción a incorporar.")
    orden: int = Field(..., ge=1, le=999, description="Semilla manual en el cuadro.")


class EquipoEditarIn(Schema):
    """Edición de la participación de un equipo en el cuadro."""

    orden: int | None = Field(default=None, ge=1, le=999, description="Nueva semilla manual.")
    estado: str | None = Field(
        default=None,
        description="Nuevo estado: `ACTIVO` o `RETIRADO`.",
    )
    expected_version: int = Field(..., description="Versión conocida del recurso.")
    motivo: str | None = Field(
        default=None,
        max_length=500,
        description="Motivo auditado de la operación.",
    )


class RondaCrearIn(Schema):
    """Alta de una ronda."""

    etiqueta: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Etiqueta de la ronda.",
    )
    orden: int = Field(..., ge=1, le=999, description="Orden de la ronda en el cuadro.")


class EncuentroCrearIn(Schema):
    """Alta de un encuentro."""

    ronda_id: str = Field(..., description="Ronda del encuentro.")
    orden: int = Field(..., ge=1, le=999, description="Orden del encuentro en la ronda.")


class EncuentroActualizarIn(Schema):
    """Edición de un encuentro.

    Un campo AUSENTE significa "no tocar". Los campos que se tocan exigen
    MOTIVO auditado.
    """

    participante_1_id: str | None = Field(
        default=None,
        description="Participación en el slot 1. `null` explícito lo vacía.",
    )
    participante_2_id: str | None = Field(
        default=None,
        description="Participación en el slot 2. `null` explícito lo vacía.",
    )
    inicio_programado: datetime | None = Field(
        default=None,
        description="Inicio del encuentro.",
    )
    fin_programado: datetime | None = Field(
        default=None,
        description="Fin del encuentro.",
    )
    siguiente_encuentro_id: str | None = Field(
        default=None,
        description="Encuentro destino del avance.",
    )
    slot_destino: str | None = Field(
        default=None,
        description="Slot del destino que recibe al ganador.",
    )
    es_bye: bool | None = Field(
        default=None,
        description="Marca el encuentro como bye manual.",
    )
    estado: str | None = Field(
        default=None,
        description=(
            "Nuevo estado del encuentro: `PROGRAMADO`, `EN_CURSO` o "
            "`CANCELADO`."
        ),
    )
    motivo: str | None = Field(
        default=None,
        max_length=500,
        description="Motivo auditado de la operación.",
    )
    expected_version: int = Field(..., description="Versión conocida del encuentro.")


class ResultadoRegistrarIn(Schema):
    """Registro del resultado autoritativo de un encuentro."""

    ganador_id: str = Field(
        ...,
        description="Participación ganadora. Debe ocupar uno de los dos slots.",
    )
    puntaje_1: int | None = Field(
        default=None,
        ge=0,
        description="Puntaje del slot 1. Informativo.",
    )
    puntaje_2: int | None = Field(
        default=None,
        ge=0,
        description="Puntaje del slot 2. Informativo.",
    )
    marcador_detalle: str | None = Field(
        default=None,
        max_length=500,
        description="Detalle informativo del marcador.",
    )
    motivo: str | None = Field(
        default=None,
        max_length=500,
        description="Motivo auditado de la operación.",
    )
    expected_version: int = Field(..., description="Versión conocida del encuentro.")


class AvanceConfirmarIn(Schema):
    """Confirmación del avance del ganador."""

    motivo: str | None = Field(
        default=None,
        max_length=500,
        description="Motivo auditado de la operación.",
    )
    expected_version: int = Field(..., description="Versión conocida del encuentro.")


class CorreccionPrevisualizarIn(Schema):
    """Vista previa del impacto de la corrección."""

    ganador_id: str = Field(
        ...,
        description="Nueva participación ganadora. Debe ocupar uno de los slots.",
    )


class CorreccionAplicarIn(Schema):
    """Aplicación de la corrección del ganador."""

    ganador_id: str = Field(
        ...,
        description="Nueva participación ganadora. Debe ocupar uno de los slots.",
    )
    motivo: str | None = Field(
        default=None,
        max_length=500,
        description="Motivo auditado OBLIGATORIO de la corrección.",
    )
    override: bool = Field(
        default=False,
        description=(
            "Autorización explícita para corregir aunque un descendiente ya "
            "haya transcurrido."
        ),
    )
    acepta_impacto: bool = Field(
        default=False,
        description="El administrador acepta el impacto calculado de la corrección.",
    )
    expected_version: int = Field(..., description="Versión conocida del encuentro.")


__all__ = [
    "AgendaOut",
    "AvanceConfirmarIn",
    "AvanceOut",
    "AvancePreviewOut",
    "CompetenciaCrearIn",
    "CompetenciaDetalleOut",
    "CompetenciaEquipoOut",
    "CompetenciaListadoOut",
    "CorreccionAplicarIn",
    "CorreccionImpactoOut",
    "CorreccionOut",
    "CorreccionPrevisualizarIn",
    "CorreccionPreviewOut",
    "EncuentroActualizarIn",
    "EncuentroCrearIn",
    "EncuentroOut",
    "EncuentroPublicoOut",
    "EncuentrosPublicosOut",
    "EquipoEditarIn",
    "EquipoElegibleOut",
    "EquipoIncorporarIn",
    "ParticipanteOut",
    "ResultadoRegistrarIn",
    "ResultadoRegistradoOut",
    "RondaCrearIn",
    "RondaOut",
]
