"""EL presenter operativo del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §3, §8

**UN SOLO PRESENTER para las TRES superficies.** La agenda, el cuadro y el
detalle del encuentro se proyectan con esta misma clase: no hay un presenter
por ruta que pueda divergir del otro (`FL-11` paso 6, `frontend/05` §3: "misma
información y acciones, sin múltiples editores divergentes").

El presenter es un TRANSFORMADOR PURO:

- recibe result objects del dominio y devuelve wrappers HTTP;
- NO consulta la base de datos, NO llama selectores y NO decide estados;
- NO construye mensajes de error (sólo el catálogo global `core/exceptions.py`
  los traduce) y NO selecciona el mensaje de éxito (es del controller).

**Lo que NO expone:** el detalle técnico de la auditoría, el SQL, los
identificadores internos del proveedor y cualquier prosa técnica. Lo que sí
expone son los ESTADOS OPERATIVOS y la CONSECUENCIA CONCRETA de cada
acción: el número de encuentros afectados por una corrección, el ocupante
actual de un slot, el motivo de un bloqueo (`frontend/05` §3, `RN-A02`).
"""

from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    AvancePreviewResult,
    AvanceResult,
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
    CompetenciaListadoResult,
    CorreccionImpactoResult,
    CorreccionPreviewResult,
    CorreccionResult,
    EncuentroResult,
    ParticipanteResult,
    ResultadoRegistradoResult,
    RondaResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EquipoElegibleData,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    AgendaOut,
    AvanceOut,
    AvancePreviewOut,
    CompetenciaDetalleOut,
    CompetenciaEquipoOut,
    CompetenciaListadoOut,
    CorreccionImpactoOut,
    CorreccionPreviewOut,
    CorreccionOut,
    EncuentroOut,
    EquipoElegibleOut,
    ParticipanteOut,
    ResultadoRegistradoOut,
    RondaOut,
)


class CompetenciasPresenter:
    """Proyección única de la operación deportiva de una edición."""

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
    def present_encuentro(result: EncuentroResult) -> EncuentroOut:
        """Proyecta un encuentro.

        Es la MISMA proyección para la agenda, el cuadro y el detalle.
        """
        return EncuentroOut(
            id=result.id,
            ronda_id=result.ronda_id,
            ronda_etiqueta=result.ronda_etiqueta,
            ronda_orden=result.ronda_orden,
            competencia_id=result.competencia_id,
            orden=result.orden,
            estado=result.estado,
            es_bye=result.es_bye,
            participantes=[
                CompetenciasPresenter.present_participante(participante)
                for participante in result.participantes
            ],
            inicio_programado=result.inicio_programado,
            fin_programado=result.fin_programado,
            puntaje_1=result.puntaje_1,
            puntaje_2=result.puntaje_2,
            marcador_detalle=result.marcador_detalle,
            ganador_equipo_id=result.ganador_equipo_id,
            ganador_equipo_nombre=result.ganador_equipo_nombre,
            siguiente_encuentro_id=result.siguiente_encuentro_id,
            slot_destino=result.slot_destino,
            iniciado_en=result.iniciado_en,
            finalizado_en=result.finalizado_en,
            version=result.version,
            acciones=list(result.acciones),
        )

    @staticmethod
    def present_ronda(result: RondaResult) -> RondaOut:
        """Proyecta una ronda con sus encuentros."""
        return RondaOut(
            id=result.id,
            etiqueta=result.etiqueta,
            orden=result.orden,
            estado=result.estado,
            version=result.version,
            encuentros=[
                CompetenciasPresenter.present_encuentro(encuentro)
                for encuentro in result.encuentros
            ],
        )

    @staticmethod
    def present_equipo(result: CompetenciaEquipoResult) -> CompetenciaEquipoOut:
        """Proyecta la participación de un equipo en el cuadro."""
        return CompetenciaEquipoOut(
            id=result.id,
            equipo_id=result.equipo_id,
            equipo_nombre=result.equipo_nombre,
            orden=result.orden,
            estado=result.estado,
            version=result.version,
        )

    # ── superficies ────────────────────────────────────────────────────────

    @staticmethod
    def present_listado(result: CompetenciaListadoResult) -> CompetenciaListadoOut:
        """Proyecta la fila de la lista de competencias."""
        return CompetenciaListadoOut(
            id=result.id,
            edicion_id=result.edicion_id,
            disciplina_id=result.disciplina_id,
            disciplina_nombre=result.disciplina_nombre,
            nombre=result.nombre,
            estado=result.estado,
            fecha=result.fecha,
            total_equipos=result.total_equipos,
            total_encuentros=result.total_encuentros,
            total_encuentros_finalizados=result.total_encuentros_finalizados,
        )

    @staticmethod
    def present_detalle(result: CompetenciaDetalleResult) -> CompetenciaDetalleOut:
        """Proyecta el detalle operativo de la competencia."""
        return CompetenciaDetalleOut(
            id=result.id,
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            disciplina_id=result.disciplina_id,
            disciplina_nombre=result.disciplina_nombre,
            nombre=result.nombre,
            estado=result.estado,
            fecha=result.fecha,
            version=result.version,
            equipos=[
                CompetenciasPresenter.present_equipo(equipo) for equipo in result.equipos
            ],
            rondas=[
                CompetenciasPresenter.present_ronda(ronda) for ronda in result.rondas
            ],
        )

    @staticmethod
    def present_cuadro(resultados: list[RondaResult]) -> list[RondaOut]:
        """Proyecta el cuadro completo de una competencia."""
        return [
            CompetenciasPresenter.present_ronda(ronda) for ronda in resultados
        ]

    @staticmethod
    def present_agenda(result: AgendaResult) -> AgendaOut:
        """Proyecta la agenda transversal del día."""
        return AgendaOut(
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            fecha=result.fecha,
            total=result.total,
            encuentros=[
                CompetenciasPresenter.present_encuentro(encuentro)
                for encuentro in result.encuentros
            ],
        )

    @staticmethod
    def present_equipos_elegibles(
        veredictos: list[EquipoElegibleData],
    ) -> list[EquipoElegibleOut]:
        """Proyecta los veredictos de elegibilidad.

        El `motivo` viaja como CÓDIGO: el backend publica la razón y el
        cliente nunca la adivina (`QA-K01`).
        """
        return [
            EquipoElegibleOut(
                equipo_id=veredicto.equipo_id,
                nombre=veredicto.nombre,
                edicion_id=veredicto.edicion_id,
                disciplina_id=veredicto.disciplina_id,
                disciplina_nombre=veredicto.disciplina_nombre,
                estado=veredicto.estado,
                es_elegible=veredicto.es_elegible,
                motivo=veredicto.motivo,
                participantes_activos=veredicto.participantes_activos,
                minimo_requerido=veredicto.minimo_requerido,
            )
            for veredicto in veredictos
        ]

    # ── operaciones ────────────────────────────────────────────────────────

    @staticmethod
    def present_resultado(result: ResultadoRegistradoResult) -> ResultadoRegistradoOut:
        """Proyecta el resultado autoritativo ya registrado."""
        return ResultadoRegistradoOut(
            encuentro=CompetenciasPresenter.present_encuentro(result.encuentro),
            ganador_equipo_id=result.ganador_equipo_id,
            ganador_equipo_nombre=result.ganador_equipo_nombre,
        )

    @staticmethod
    def present_avance_preview(result: AvancePreviewResult) -> AvancePreviewOut:
        """Proyecta la vista previa del avance."""
        return AvancePreviewOut(
            encuentro_id=result.encuentro_id,
            siguiente_encuentro_id=result.siguiente_encuentro_id,
            slot_destino=result.slot_destino,
            ganador_equipo_id=result.ganador_equipo_id,
            ganador_equipo_nombre=result.ganador_equipo_nombre,
            ocupante_actual_equipo_id=result.ocupante_actual_equipo_id,
            ya_propagado=result.ya_propagado,
            bloqueado=result.bloqueado,
            motivo_bloqueo=result.motivo_bloqueo,
            puede_confirmar=result.puede_confirmar,
        )

    @staticmethod
    def present_avance(result: AvanceResult) -> AvanceOut:
        """Proyecta el avance confirmado."""
        return AvanceOut(
            encuentro_origen_id=result.encuentro_origen_id,
            siguiente_encuentro_id=result.siguiente_encuentro_id,
            slot_destino=result.slot_destino,
            ganador_equipo_id=result.ganador_equipo_id,
            ganador_equipo_nombre=result.ganador_equipo_nombre,
            ya_aplicado=result.ya_aplicado,
            destino=CompetenciasPresenter.present_encuentro(result.destino),
        )

    @staticmethod
    def present_impacto(result: CorreccionImpactoResult) -> CorreccionImpactoOut:
        """Proyecta el impacto de la corrección sobre un descendiente."""
        return CorreccionImpactoOut(
            encuentro_id=result.encuentro_id,
            slot=result.slot,
            bloqueado=result.bloqueado,
            motivo_bloqueo=result.motivo_bloqueo,
            reemplaza=result.reemplaza,
            limpia_slot=result.limpia_slot,
            limpia_resultado=result.limpia_resultado,
            afecta=result.afecta,
        )

    @staticmethod
    def present_correccion_preview(
        result: CorreccionPreviewResult,
    ) -> CorreccionPreviewOut:
        """Proyecta la vista previa del impacto de la corrección."""
        return CorreccionPreviewOut(
            encuentro_id=result.encuentro_id,
            ganador_actual_equipo_id=result.ganador_actual_equipo_id,
            ganador_nuevo_equipo_id=result.ganador_nuevo_equipo_id,
            ganador_nuevo_equipo_nombre=result.ganador_nuevo_equipo_nombre,
            requiere_override=result.requiere_override,
            total_afectados=result.total_afectados,
            descendientes=[
                CompetenciasPresenter.present_impacto(descendiente)
                for descendiente in result.descendientes
            ],
            puede_confirmar=result.puede_confirmar,
        )

    @staticmethod
    def present_correccion(result: CorreccionResult) -> CorreccionOut:
        """Proyecta la corrección aplicada."""
        return CorreccionOut(
            encuentro_id=result.encuentro_id,
            ganador_nuevo_equipo_id=result.ganador_nuevo_equipo_id,
            ganador_nuevo_equipo_nombre=result.ganador_nuevo_equipo_nombre,
            descendientes_afectados=result.descendientes_afectados,
            override_aplicado=result.override_aplicado,
            encuentro=CompetenciasPresenter.present_encuentro(result.encuentro),
            descendientes=[
                CompetenciasPresenter.present_impacto(descendiente)
                for descendiente in result.descendientes
            ],
        )


__all__ = ["CompetenciasPresenter"]
