"""DTOs INTERNOS del módulo `competencias` (no son esquemas HTTP).

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6

Los DTOs de `domain/schemas/` viajan entre el DOMINIO y la capa de
presentación. Los de `domain/results/` son la SALIDA de los servicios: el
presenter los proyecta a los esquemas HTTP.

Este archivo NO contiene esquemas HTTP: los de la capa HTTP viven en
`presentation/schemas/`.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class EquipoElegibleData(BaseModel):
    """El VEREDICTO de elegibilidad de un equipo para una competencia.

    Lo produce el PUERTO `IEquipoElegibleService`, que consulta a
    `modules.salesianos_fest` (el dueño de la inscripción). Este módulo no
    decide: traduce el veredicto a una excepción con motivo de máquina.

    `motivo` es el código de `MotivoNoElegibilidad`: el backend publica la
    RAZÓN concreta del rechazo (`QA-K01`).
    """

    equipo_id: str = Field(..., description="Equipo de inscripción evaluado.")
    nombre: str = Field(..., description="Nombre del equipo.")
    edicion_id: str = Field(..., description="Edición a la que pertenece el equipo.")
    disciplina_id: str = Field(..., description="Disciplina del equipo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    estado: str = Field(..., description="Estado del equipo en su inscripción.")
    es_elegible: bool = Field(..., description="Si el equipo puede competir.")
    motivo: str = Field(
        ...,
        description="Código de `MotivoNoElegibilidad` con la razón del veredicto.",
    )
    participantes_activos: int = Field(
        ...,
        ge=0,
        description="Participantes ACTIVOS del equipo en el pool de la inscripción.",
    )
    minimo_requerido: int = Field(
        ...,
        ge=0,
        description="Mínimo de participantes que exige la disciplina.",
    )


class CompetenciaCreateData(BaseModel):
    """Datos de creación de una competencia."""

    edicion_id: str = Field(..., description="Edición de la competencia.")
    disciplina_id: str = Field(..., description="Disciplina del torneo.")
    nombre: str = Field(..., max_length=200, description="Nombre del torneo.")
    fecha: date = Field(..., description="Día de la competencia.")


class EquipoCompetenciaCreateData(BaseModel):
    """Datos de incorporación de un equipo al cuadro."""

    competencia_id: str = Field(..., description="Competencia que incorpora al equipo.")
    equipo_id: str = Field(..., description="Equipo de inscripción a incorporar.")
    orden: int = Field(..., ge=1, description="Semilla manual en el cuadro.")


class EquipoCompetenciaEditData(BaseModel):
    """Datos de edición de la participación de un equipo en el cuadro."""

    orden: int | None = Field(default=None, ge=1, description="Nueva semilla manual.")
    estado: str | None = Field(
        default=None,
        description="Nuevo estado: `ACTIVO` o `RETIRADO`.",
    )


class RondaCreateData(BaseModel):
    """Datos de creación de una ronda."""

    competencia_id: str = Field(..., description="Competencia de la ronda.")
    etiqueta: str = Field(..., max_length=80, description="Etiqueta de la ronda.")
    orden: int = Field(..., ge=1, description="Orden de la ronda en el cuadro.")


class EncuentroCreateData(BaseModel):
    """Datos de creación de un encuentro."""

    ronda_id: str = Field(..., description="Ronda del encuentro.")
    orden: int = Field(..., ge=1, description="Orden del encuentro en la ronda.")


class EncuentroActualizarData(BaseModel):
    """Datos de actualización de un encuentro.

    Un campo ausente significa "no tocar". Los campos que se tocan son los
    protegidos y exigen MOTIVO (`RN-K02`).
    """

    participante_1_id: str | None = Field(
        default=None,
        description="Participación en el slot 1. `None` explícito lo vacía.",
    )
    participante_2_id: str | None = Field(
        default=None,
        description="Participación en el slot 2. `None` explícito lo vacía.",
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
            "`CANCELADO`. El sistema NO avanza de estado por su cuenta: "
            "`EN_CURSO` es el único estado que acepta un resultado."
        ),
    )
    motivo: str | None = Field(
        default=None,
        description="Motivo auditado de la operación.",
    )


class ResultadoEncuentroData(BaseModel):
    """Datos del resultado autoritativo de un encuentro."""

    ganador_id: str = Field(
        ...,
        description="Participación ganadora. Debe ocupar uno de los dos slots.",
    )
    puntaje_1: int | None = Field(
        default=None,
        ge=0,
        description="Puntaje del slot 1. Informativo: no decide el ganador.",
    )
    puntaje_2: int | None = Field(
        default=None,
        ge=0,
        description="Puntaje del slot 2. Informativo: no decide el ganador.",
    )
    marcador_detalle: str | None = Field(
        default=None,
        max_length=500,
        description="Detalle informativo del marcador.",
    )
    motivo: str | None = Field(
        default=None,
        description="Motivo auditado de la operación.",
    )


class AvanceData(BaseModel):
    """Datos de la confirmación del avance del ganador."""

    motivo: str | None = Field(
        default=None,
        description="Motivo auditado de la operación.",
    )


class CorreccionData(BaseModel):
    """Datos de la corrección del ganador de un encuentro."""

    ganador_id: str = Field(
        ...,
        description="Nueva participación ganadora. Debe ocupar uno de los slots.",
    )
    motivo: str | None = Field(
        default=None,
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


__all__ = [
    "AvanceData",
    "CompetenciaCreateData",
    "CorreccionData",
    "EncuentroActualizarData",
    "EncuentroCreateData",
    "EquipoCompetenciaCreateData",
    "EquipoCompetenciaEditData",
    "EquipoElegibleData",
    "ResultadoEncuentroData",
    "RondaCreateData",
]
