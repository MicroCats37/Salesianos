"""
Presenters of the competencias module — pure transformers.

A presenter receives a DOMAIN RESULT and returns an HTTP SCHEMA. It never
queries the database, never calls a selector and never builds an error
response (`contract/api-wrapper-presenter-contract.md` §3,
`contract/PLAN_REFACTORIZACION.md` §3.A).

Every method is a `@staticmethod`: the presenter holds no state.
"""
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    AvancePreviewResult,
    AvanceResult,
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
    CompetenciaListadoResult,
    CorreccionPreviewResult,
    CorreccionResult,
    CuadroResult,
    EncuentroResult,
    RondaResult,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    AgendaOut,
    AvanceOut,
    AvancePreviewOut,
    CompetenciaDetalleOut,
    CompetenciaEquipoOut,
    CompetenciaListOut,
    CorreccionOut,
    CorreccionPreviewOut,
    CuadroOut,
    EncuentroOut,
    ImpactoDescendienteOut,
    RondaCuadroOut,
    RondaOut,
)


class CompetenciasPresenter:
    """Transformers of the results of the module into HTTP schemas."""

    # ── lecturas ───────────────────────────────────────────────────────────

    @staticmethod
    def present_listado(
        resultados: list[CompetenciaListadoResult],
    ) -> list[CompetenciaListOut]:
        """Map the rows of the list of competitions."""
        return [
            CompetenciasPresenter.present_competencia(resultado)
            for resultado in resultados
        ]

    @staticmethod
    def present_competencia(resultado) -> CompetenciaListOut:
        """Map ONE competition (of a read or of a command)."""
        return CompetenciaListOut(
            id=resultado.id,
            evento_id=resultado.evento_id,
            disciplina_id=resultado.disciplina_id,
            categoria_id=resultado.categoria_id,
            nombre=resultado.nombre,
            fecha=resultado.fecha,
            estado=resultado.estado,
            version=resultado.version,
            total_equipos=getattr(resultado, "total_equipos", 0),
            total_encuentros=getattr(resultado, "total_encuentros", 0),
            total_encuentros_finalizados=getattr(
                resultado, "total_encuentros_finalizados", 0
            ),
        )

    @staticmethod
    def present_detalle(resultado: CompetenciaDetalleResult) -> CompetenciaDetalleOut:
        """Map the detail of a competition."""
        return CompetenciaDetalleOut(
            id=resultado.id,
            evento_id=resultado.evento_id,
            disciplina_id=resultado.disciplina_id,
            categoria_id=resultado.categoria_id,
            nombre=resultado.nombre,
            fecha=resultado.fecha,
            estado=resultado.estado,
            version=resultado.version,
            total_equipos=resultado.total_equipos,
            total_encuentros=resultado.total_encuentros,
            total_encuentros_finalizados=resultado.total_encuentros_finalizados,
            created_at=resultado.created_at,
            equipos=CompetenciasPresenter.present_equipos(resultado.equipos),
            rondas=CompetenciasPresenter.present_rondas(resultado.rondas),
        )

    @staticmethod
    def present_equipos(
        resultados: list[CompetenciaEquipoResult],
    ) -> list[CompetenciaEquipoOut]:
        """Map the teams of the bracket."""
        return [
            CompetenciaEquipoOut(
                id=resultado.id,
                competencia_id=resultado.competencia_id,
                equipo_id=resultado.equipo_id,
                equipo_nombre=resultado.equipo_nombre,
                orden=resultado.orden,
                estado=resultado.estado,
                version=resultado.version,
            )
            for resultado in resultados
        ]

    @staticmethod
    def present_rondas(resultados: list[RondaResult]) -> list[RondaOut]:
        """Map the rounds of the bracket."""
        return [
            RondaOut(
                id=resultado.id,
                competencia_id=resultado.competencia_id,
                etiqueta=resultado.etiqueta,
                orden=resultado.orden,
                estado=resultado.estado,
                version=resultado.version,
                total_encuentros=resultado.total_encuentros,
            )
            for resultado in resultados
        ]

    @staticmethod
    def present_encuentros(
        resultados: list[EncuentroResult],
    ) -> list[EncuentroOut]:
        """Map the encounters of the bracket."""
        return [
            CompetenciasPresenter.present_encuentro(resultado)
            for resultado in resultados
        ]

    @staticmethod
    def present_encuentro(resultado: EncuentroResult) -> EncuentroOut:
        """Map ONE encounter."""
        return EncuentroOut(
            id=resultado.id,
            ronda_id=resultado.ronda_id,
            ronda_etiqueta=resultado.ronda_etiqueta,
            ronda_orden=resultado.ronda_orden,
            competencia_id=resultado.competencia_id,
            competencia_nombre=resultado.competencia_nombre,
            orden=resultado.orden,
            participante_1_id=resultado.participante_1_id,
            participante_1_nombre=resultado.participante_1_nombre,
            participante_2_id=resultado.participante_2_id,
            participante_2_nombre=resultado.participante_2_nombre,
            inicio_programado=resultado.inicio_programado,
            fin_programado=resultado.fin_programado,
            estado=resultado.estado,
            estado_pre_suspension=resultado.estado_pre_suspension,
            iniciado_en=resultado.iniciado_en,
            finalizado_en=resultado.finalizado_en,
            es_bye=resultado.es_bye,
            ganador_id=resultado.ganador_id,
            puntaje_1=resultado.puntaje_1,
            puntaje_2=resultado.puntaje_2,
            marcador_detalle=resultado.marcador_detalle,
            siguiente_encuentro_id=resultado.siguiente_encuentro_id,
            slot_destino=resultado.slot_destino,
            ganador_propagado_id=resultado.ganador_propagado_id,
            version=resultado.version,
        )

    @staticmethod
    def present_cuadro(resultado: CuadroResult) -> CuadroOut:
        """Map the bracket of a competition."""
        return CuadroOut(
            competencia_id=resultado.competencia_id,
            nombre=resultado.nombre,
            fecha=resultado.fecha,
            estado=resultado.estado,
            total_equipos=resultado.total_equipos,
            rondas=[
                RondaCuadroOut(
                    id=columna.id,
                    etiqueta=columna.etiqueta,
                    orden=columna.orden,
                    estado=columna.estado,
                    encuentros=[
                        CompetenciasPresenter.present_encuentro(encuentro)
                        for encuentro in columna.encuentros
                    ],
                )
                for columna in resultado.rondas
            ],
        )

    @staticmethod
    def present_agenda(resultado: AgendaResult) -> AgendaOut:
        """Map the agenda of one day."""
        return AgendaOut(
            fecha=resultado.fecha,
            total=resultado.total,
            encuentros=CompetenciasPresenter.present_encuentros(
                resultado.encuentros
            ),
        )

    # ── comandos ───────────────────────────────────────────────────────────

    @staticmethod
    def present_avance_preview(resultado: AvancePreviewResult) -> AvancePreviewOut:
        """Map the proposal of the propagation of the winner."""
        return AvancePreviewOut(
            encuentro_id=resultado.encuentro_id,
            siguiente_encuentro_id=resultado.siguiente_encuentro_id,
            slot_destino=resultado.slot_destino,
            ganador_id=resultado.ganador_id,
            ocupante_actual_id=resultado.ocupante_actual_id,
            ya_propagado=resultado.ya_propagado,
            bloqueado=resultado.bloqueado,
            motivo_bloqueo=resultado.motivo_bloqueo,
        )

    @staticmethod
    def present_avance(resultado: AvanceResult) -> AvanceOut:
        """Map the outcome of the propagation of the winner."""
        return AvanceOut(
            encuentro_origen_id=resultado.encuentro_origen_id,
            siguiente_encuentro_id=resultado.siguiente_encuentro_id,
            slot_destino=resultado.slot_destino,
            ganador_id=resultado.ganador_id,
            ya_aplicado=resultado.ya_aplicado,
            destino=CompetenciasPresenter.present_encuentro(resultado.destino),
        )

    @staticmethod
    def present_correccion_preview(
        resultado: CorreccionPreviewResult,
    ) -> CorreccionPreviewOut:
        """Map the impact analysis of the correction."""
        return CorreccionPreviewOut(
            encuentro_id=resultado.encuentro_id,
            ganador_actual_id=resultado.ganador_actual_id,
            ganador_nuevo_id=resultado.ganador_nuevo_id,
            requiere_override=resultado.requiere_override,
            descendientes=[
                CompetenciasPresenter.present_impacto(impacto)
                for impacto in resultado.descendientes
            ],
        )

    @staticmethod
    def present_correccion(resultado: CorreccionResult) -> CorreccionOut:
        """Map the outcome of the correction."""
        return CorreccionOut(
            encuentro_id=resultado.encuentro_id,
            ganador_id=resultado.ganador_id,
            requirio_override=resultado.requirio_override,
            descendientes_afectados=resultado.descendientes_afectados,
            encuentro=CompetenciasPresenter.present_encuentro(resultado.encuentro),
            descendientes=[
                CompetenciasPresenter.present_impacto(impacto)
                for impacto in resultado.descendientes
            ],
        )

    @staticmethod
    def present_impacto(resultado) -> ImpactoDescendienteOut:
        """Map the impact of the correction over one descendant."""
        return ImpactoDescendienteOut(
            encuentro_id=resultado.encuentro_id,
            slot=resultado.slot,
            estado=resultado.estado,
            ocupante_actual_id=resultado.ocupante_actual_id,
            ganador_propagado_id=resultado.ganador_propagado_id,
            bloqueado=resultado.bloqueado,
            motivo_bloqueo=resultado.motivo_bloqueo,
            se_reemplaza=resultado.se_reemplaza,
            se_limpia_resultado=resultado.se_limpia_resultado,
        )


__all__ = ["CompetenciasPresenter"]
