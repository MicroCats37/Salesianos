"""`CompetenciasOrchestrator` — la fachada async del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5

Fachada MUY DELGADA: delega en los flujos y en los selectores y devuelve
result objects, NUNCA schemas HTTP. No contiene lógica de negocio.

**Un método por ruta.** Cada método corresponde a una operación de la
superficie HTTP; el controlador las llama una a una.

**El alcance de edición se resuelve AQUÍ**, en la frontera HTTP, y no en el
dominio: las rutas que no llevan la edición en el camino (la lista y la
agenda) la resuelven con el ORDEN CONGELADO de `FR-02` §2.2, a través del
puerto `IAlcanceEdicion`. Las rutas que sí la llevan (todo lo que cuelga de
una competencia) la toman de la competencia, que es su alcance (`RN-E01`).
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.competencias.domain.ports import IAlcanceEdicion, IEquipoElegibleService
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    AvancePreviewResult,
    AvanceResult,
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
    CompetenciaListadoResult,
    CorreccionPreviewResult,
    CorreccionResult,
    EncuentroResult,
    ResultadoRegistradoResult,
    RondaResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    AvanceData,
    CompetenciaCreateData,
    CorreccionData,
    EncuentroActualizarData,
    EncuentroCreateData,
    EquipoCompetenciaCreateData,
    EquipoCompetenciaEditData,
    EquipoElegibleData,
    ResultadoEncuentroData,
    RondaCreateData,
)
from modules.competencias.domain.selectors.competencia_selector import (
    CompetenciaSelector,
)
from modules.competencias.domain.selectors.encuentro_selector import (
    EncuentroSelector,
)
from modules.competencias.domain.services.flujos.avance_flujo import AvanceFlujo
from modules.competencias.domain.services.flujos.correccion_flujo import CorreccionFlujo
from modules.competencias.domain.services.flujos.cuadro_flujo import CuadroFlujo
from modules.competencias.domain.services.flujos.encuentro_flujo import EncuentroFlujo
from modules.competencias.domain.services.flujos.resultado_flujo import ResultadoFlujo


class CompetenciasOrchestrator:
    """Fachada async de la operación deportiva de una edición."""

    @inject
    def __init__(
        self,
        cuadro_flujo: CuadroFlujo,
        encuentro_flujo: EncuentroFlujo,
        resultado_flujo: ResultadoFlujo,
        avance_flujo: AvanceFlujo,
        correccion_flujo: CorreccionFlujo,
        competencia_selector: CompetenciaSelector,
        encuentro_selector: EncuentroSelector,
        alcance: IAlcanceEdicion,
        elegibilidad: IEquipoElegibleService,
    ):
        self.cuadro_flujo = cuadro_flujo
        self.encuentro_flujo = encuentro_flujo
        self.resultado_flujo = resultado_flujo
        self.avance_flujo = avance_flujo
        self.correccion_flujo = correccion_flujo
        self.competencia_selector = competencia_selector
        self.encuentro_selector = encuentro_selector
        self.alcance = alcance
        self.elegibilidad = elegibilidad

    # ── lecturas ───────────────────────────────────────────────────────────

    async def listar_competencias(
        self,
        *,
        disciplina_id=None,
        estado=None,
    ) -> list[CompetenciaListadoResult]:
        """Las competencias de la edición vigente, con sus contadores."""
        edicion = await sync_to_async(self._edicion_actual)()
        return await sync_to_async(self.competencia_selector.listar)(
            edicion.id,
            disciplina_id=disciplina_id,
            estado=estado,
        )

    async def obtener_competencia(self, competencia_id) -> CompetenciaDetalleResult:
        """El detalle operativo de la competencia: equipos y cuadro."""
        return await sync_to_async(self.competencia_selector.detalle)(competencia_id)

    async def obtener_cuadro(self, competencia_id) -> list[RondaResult]:
        """El cuadro de la competencia: rondas y encuentros."""
        return await sync_to_async(self.encuentro_selector.rondas)(competencia_id)

    async def obtener_agenda(self, dia) -> AgendaResult:
        """La agenda transversal del día en la edición vigente."""
        edicion = await sync_to_async(self._edicion_actual)()
        return await sync_to_async(self.encuentro_selector.agenda)(
            edicion.id,
            dia,
            edicion.nombre,
        )

    async def listar_equipos_elegibles(
        self,
        competencia_id,
    ) -> list[EquipoElegibleData]:
        """Los equipos CANDIDATOS de la competencia y su veredicto.

        El veredicto lo produce el DUEÑO de la inscripción
        (`IEquipoElegibleService`): este módulo no reimplementa ninguna regla
        de elegibilidad (`RN-K01`). Cada veredicto lleva el MOTIVO del
        rechazo para que la interfaz pueda explicarlo (`frontend/05` §4).
        """
        competencia = await sync_to_async(self.competencia_selector.obtener_por_id)(
            competencia_id
        )
        return await sync_to_async(self.elegibilidad.listar_equipos_elegibles)(
            str(competencia.edicion_id),
            str(competencia.disciplina_id),
        )

    # ── escrituras ─────────────────────────────────────────────────────────

    async def crear_competencia(
        self,
        data: CompetenciaCreateData,
        *,
        actor=None,
    ) -> CompetenciaDetalleResult:
        """Crea la competencia en la edición pedida."""
        return await self.cuadro_flujo.crear_competencia(data, actor=actor)

    async def incorporar_equipo(
        self,
        competencia_id,
        data: EquipoCompetenciaCreateData,
        *,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Incorpora un equipo elegible al cuadro."""
        return await self.cuadro_flujo.incorporar_equipo(
            competencia_id,
            data,
            actor=actor,
        )

    async def editar_equipo(
        self,
        competencia_id,
        participacion_id,
        data: EquipoCompetenciaEditData,
        *,
        expected_version: int | None,
        motivo: str | None,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Edita la semilla o el estado de la participación."""
        return await self.cuadro_flujo.editar_equipo(
            competencia_id,
            participacion_id,
            data,
            expected_version=expected_version,
            motivo=motivo,
            actor=actor,
        )

    async def crear_ronda(
        self,
        competencia_id,
        data: RondaCreateData,
        *,
        actor=None,
    ) -> RondaResult:
        """Crea una ronda del cuadro."""
        return await self.cuadro_flujo.crear_ronda(competencia_id, data, actor=actor)

    async def crear_encuentro(
        self,
        competencia_id,
        ronda_id,
        data: EncuentroCreateData,
        *,
        actor=None,
    ) -> EncuentroResult:
        """Crea un encuentro en la ronda."""
        return await self.cuadro_flujo.crear_encuentro(
            competencia_id,
            ronda_id,
            data,
            actor=actor,
        )

    async def actualizar_encuentro(
        self,
        competencia_id,
        encuentro_id,
        data: EncuentroActualizarData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> EncuentroResult:
        """Aplica los cambios declarados en el comando de edición."""
        return await self.encuentro_flujo.actualizar_encuentro(
            competencia_id,
            encuentro_id,
            data,
            expected_version=expected_version,
            actor=actor,
        )

    async def registrar_resultado(
        self,
        competencia_id,
        encuentro_id,
        data: ResultadoEncuentroData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> ResultadoRegistradoResult:
        """Registra el ganador autoritativo del encuentro."""
        return await self.resultado_flujo.registrar(
            competencia_id,
            encuentro_id,
            data,
            expected_version=expected_version,
            actor=actor,
        )

    async def previsualizar_avance(
        self,
        competencia_id,
        encuentro_id,
    ) -> AvancePreviewResult:
        """La vista previa del avance. NO escribe."""
        return await self.avance_flujo.previsualizar(competencia_id, encuentro_id)

    async def confirmar_avance(
        self,
        competencia_id,
        encuentro_id,
        data: AvanceData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> AvanceResult:
        """Confirma el avance del ganador al destino."""
        return await self.avance_flujo.confirmar(
            competencia_id,
            encuentro_id,
            data,
            expected_version=expected_version,
            actor=actor,
        )

    async def previsualizar_correccion(
        self,
        competencia_id,
        encuentro_id,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """La vista previa del impacto de la corrección. NO escribe."""
        return await self.correccion_flujo.previsualizar(
            competencia_id,
            encuentro_id,
            ganador_nuevo_id,
        )

    async def corregir(
        self,
        competencia_id,
        encuentro_id,
        data: CorreccionData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> CorreccionResult:
        """Aplica la corrección con su impacto explícito."""
        return await self.correccion_flujo.corregir(
            competencia_id,
            encuentro_id,
            data,
            expected_version=expected_version,
            actor=actor,
        )

    # ── internos ───────────────────────────────────────────────────────────

    def _edicion_actual(self):
        """La edición vigente, según el ORDEN CONGELADO de `FR-02` §2.2."""
        return self.alcance.resolver_actual()


__all__ = ["CompetenciasOrchestrator"]
