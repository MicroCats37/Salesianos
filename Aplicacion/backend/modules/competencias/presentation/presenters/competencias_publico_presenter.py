"""EL presenter PÚBLICO del módulo `competencias`.

Change: `partidos-marcadores-competencias` · Batch 1

Contract: `contract/api-wrapper-presenter-contract.md` §2, §3 ·
          `contract/django-app-architecture-contract.md` §4.9

Es un TRANSFORMADOR PURO: recibe result objects del dominio y devuelve
wrappers HTTP. NO consulta la base de datos, NO llama selectores, NO
construye mensajes de error y NO selecciona el mensaje de éxito.

**La forma PÚBLICA del encuentro no es una forma nueva de DATOS.** Cada
encuentro sale de `proyectar_encuentro` —la MISMA proyección canónica que la
agenda, el cuadro y el detalle— y este presenter sólo la ENVUELVE: publica el
estado PÚBLICO (el cubo que el DOMINIO define en `domain/constants.py`) y
descarta las acciones de administración, que no existen para el público.

**El ganador NO se deduce del marcador.** `ganador_equipo_id` viaja como lo
que es: la autoridad de la progresión. Los puntajes son INFORMATIVOS y el
cliente tampoco puede deducir el ganador de ellos (`explore` §9).
"""

from modules.competencias.domain.constants import ESTADO_PUBLICO_POR_ESTADO
from modules.competencias.domain.results.competencias_results import (
    EncuentroResult,
    EncuentrosPublicosResult,
    ParticipanteResult,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    EncuentroPublicoOut,
    EncuentrosPublicosOut,
    ParticipanteOut,
)


class CompetenciasPublicoPresenter:
    """La proyección PÚBLICA de los encuentros de la edición."""

    # ── elementos ──────────────────────────────────────────────────────────

    @staticmethod
    def present_participante(result: ParticipanteResult) -> ParticipanteOut:
        """Proyecta un slot del encuentro."""
        return ParticipanteOut(
            slot=result.slot,
            competencia_equipo_id=result.competencia_equipo_id,
            equipo_id=result.equipo_id,
            equipo_nombre=result.equipo_nombre,
            orden=result.orden,
        )

    @staticmethod
    def present_encuentro(result: EncuentroResult) -> EncuentroPublicoOut:
        """Proyecta un encuentro a su forma PÚBLICA.

        El `estado_publico` sale de la tabla que publica el DOMINIO: el
        presenter no decide el cubo, lo aplica. La indexación es directa
        porque el selector sólo publica encuentros con cubo.
        """
        return EncuentroPublicoOut(
            id=result.id,
            ronda_id=result.ronda_id,
            ronda_etiqueta=result.ronda_etiqueta,
            ronda_orden=result.ronda_orden,
            competencia_id=result.competencia_id,
            orden=result.orden,
            estado_publico=ESTADO_PUBLICO_POR_ESTADO[result.estado],
            es_bye=result.es_bye,
            participantes=[
                CompetenciasPublicoPresenter.present_participante(participante)
                for participante in result.participantes
            ],
            inicio_programado=result.inicio_programado,
            fin_programado=result.fin_programado,
            iniciado_en=result.iniciado_en,
            finalizado_en=result.finalizado_en,
            puntaje_1=result.puntaje_1,
            puntaje_2=result.puntaje_2,
            marcador_detalle=result.marcador_detalle,
            ganador_equipo_id=result.ganador_equipo_id,
            ganador_equipo_nombre=result.ganador_equipo_nombre,
            version=result.version,
        )

    # ── superficies ────────────────────────────────────────────────────────

    @staticmethod
    def present_encuentros(result: EncuentrosPublicosResult) -> EncuentrosPublicosOut:
        """Proyecta la superficie pública completa de la edición."""
        return EncuentrosPublicosOut(
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            total=result.total,
            en_vivo=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.en_vivo
            ],
            proximos=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.proximos
            ],
            finalizados=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.finalizados
            ],
        )


__all__ = ["CompetenciasPublicoPresenter"]
