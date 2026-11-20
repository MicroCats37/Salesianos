"""PROYECCIÓN del dominio a los `results` operativos.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §3 ·
          `contract/django-app-architecture-contract.md` §4.12

Este archivo es el ÚNICO lugar donde un modelo de Django se proyecta a un
`result`. Por eso la agenda, el cuadro y el detalle del encuentro muestran
SIEMPRE los MISMOS datos (`FL-11` paso 6): no hay tres proyecciones que
puedan divergir.

**El selector carga, este archivo proyecta.** Ninguno de los dos decide
reglas de negocio: las decisiones viven en los servicios core.
"""

from modules.competencias.domain.constants import EstadoEncuentro, SlotDestino
from modules.competencias.domain.results.competencias_results import (
    CompetenciaEquipoResult,
    EncuentroResult,
    ParticipanteResult,
    RondaResult,
)

#: Acciones que el backend ADMITE en cada estado del encuentro.
#:
#: La interfaz las usa para ocultar lo imposible, pero la autorización
#: definitiva es del backend (`RN-A01`): la lista es INFORMATIVA, no una
#: puerta. Un estado terminal no admite cambios.
ACCIONES_POR_ESTADO: dict[str, tuple[str, ...]] = {
    EstadoEncuentro.BORRADOR: (
        "asignar_participantes",
        "programar",
        "enlazar",
        "marcar_bye",
    ),
    EstadoEncuentro.PROGRAMADO: (
        "iniciar",
        "desprogramar",
        "enlazar",
        "marcar_bye",
    ),
    EstadoEncuentro.EN_CURSO: (
        "registrar_resultado",
        "cancelar",
    ),
    EstadoEncuentro.FINALIZADO: (
        "corregir",
    ),
    EstadoEncuentro.CANCELADO: (),
}


def acciones_del_encuentro(encuentro) -> list[str]:
    """Las acciones que el backend admite en el estado actual.

    El avance sólo se ofrece a un encuentro FINALIZADO que tiene destino: sin
    destino no hay avance que confirmar (`RN-K02`).
    """
    acciones = list(ACCIONES_POR_ESTADO.get(encuentro.estado, ()))
    if (
        acciones
        and "corregir" in acciones
        and encuentro.siguiente_encuentro_id
        and encuentro.slot_destino
    ):
        acciones.append("avanzar")
    return acciones


def proyectar_participante(slot: str, competencia_equipo) -> ParticipanteResult:
    """Proyecta un slot del encuentro.

    Un slot libre se proyecta con todos sus identificadores vacíos: el
    frontend/05 §1.3 admite un cuadro vacío o parcial.
    """
    if competencia_equipo is None:
        return ParticipanteResult(slot=slot)
    equipo = getattr(competencia_equipo, "equipo", None)
    return ParticipanteResult(
        slot=slot,
        competencia_equipo_id=str(competencia_equipo.id),
        equipo_id=str(competencia_equipo.equipo_id),
        equipo_nombre=equipo.nombre if equipo is not None else "",
        orden=competencia_equipo.orden,
    )


def proyectar_encuentro(encuentro) -> EncuentroResult:
    """Proyecta un encuentro a su forma canónica.

    Es la MISMA forma que consumen la agenda, el cuadro y el detalle.
    """
    ganador = getattr(encuentro, "ganador", None)
    ganador_equipo = getattr(ganador, "equipo", None) if ganador is not None else None
    ronda = encuentro.ronda
    return EncuentroResult(
        id=str(encuentro.id),
        ronda_id=str(encuentro.ronda_id),
        ronda_etiqueta=ronda.etiqueta,
        ronda_orden=ronda.orden,
        competencia_id=str(ronda.competencia_id),
        orden=encuentro.orden,
        estado=encuentro.estado,
        es_bye=encuentro.es_bye,
        participantes=[
            proyectar_participante(SlotDestino.PARTICIPANTE_1, encuentro.participante_1),
            proyectar_participante(SlotDestino.PARTICIPANTE_2, encuentro.participante_2),
        ],
        inicio_programado=encuentro.inicio_programado,
        fin_programado=encuentro.fin_programado,
        puntaje_1=encuentro.puntaje_1,
        puntaje_2=encuentro.puntaje_2,
        marcador_detalle=encuentro.marcador_detalle or "",
        ganador_equipo_id=(
            str(ganador.equipo_id) if ganador is not None else None
        ),
        ganador_equipo_nombre=(
            ganador_equipo.nombre if ganador_equipo is not None else None
        ),
        siguiente_encuentro_id=(
            str(encuentro.siguiente_encuentro_id)
            if encuentro.siguiente_encuentro_id
            else None
        ),
        slot_destino=encuentro.slot_destino,
        iniciado_en=encuentro.iniciado_en,
        finalizado_en=encuentro.finalizado_en,
        version=encuentro.version,
        acciones=acciones_del_encuentro(encuentro),
    )


def proyectar_equipo(participacion) -> CompetenciaEquipoResult:
    """Proyecta la participación de un equipo en el cuadro."""
    equipo = getattr(participacion, "equipo", None)
    return CompetenciaEquipoResult(
        id=str(participacion.id),
        equipo_id=str(participacion.equipo_id),
        equipo_nombre=equipo.nombre if equipo is not None else "",
        orden=participacion.orden,
        estado=participacion.estado,
        version=participacion.version,
    )


def proyectar_ronda(ronda, encuentros) -> RondaResult:
    """Proyecta una ronda con sus encuentros ya proyectados."""
    return RondaResult(
        id=str(ronda.id),
        etiqueta=ronda.etiqueta,
        orden=ronda.orden,
        estado=ronda.estado,
        version=ronda.version,
        encuentros=[proyectar_encuentro(encuentro) for encuentro in encuentros],
    )


__all__ = [
    "ACCIONES_POR_ESTADO",
    "acciones_del_encuentro",
    "proyectar_encuentro",
    "proyectar_equipo",
    "proyectar_participante",
    "proyectar_ronda",
]
