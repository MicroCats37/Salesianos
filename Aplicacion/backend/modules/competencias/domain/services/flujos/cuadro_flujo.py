"""`CuadroFlujo` — el ALTA de la estructura del cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.

Alcance de este flujo:

- alta de la **competencia** (con su edición y su disciplina resueltas por el
  servidor);
- **incorporación** de un equipo elegible (la elegibilidad la decide el
  dueño de la inscripción y aquí se CONSUME por el puerto, `RN-K01`);
- **edición** de la participación (semilla manual y retirada);
- alta de **rondas** y de **encuentros**.

La actualización de un encuentro (participantes, horario, bye, enlace y
estado) vive en `EncuentroFlujo`: son comandos distintos, con reglas
distintas.
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.ports import IAlcanceEdicion, IEquipoElegibleService
from modules.competencias.domain.results.competencias_results import (
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaCreateData,
    EquipoCompetenciaCreateData,
    EquipoCompetenciaEditData,
    RondaCreateData,
)
from modules.competencias.domain.selectors.competencia_selector import (
    CompetenciaSelector,
)
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.competencia_core_service import (
    CompetenciaCoreService,
    CompetenciaEquipoCoreService,
    RondaCoreService,
)
from modules.competencias.domain.services.core.encuentro_core_service import (
    EncuentroCoreService,
)


class CuadroFlujo:
    """Casos de uso de alta del cuadro de una competencia."""

    @inject
    def __init__(
        self,
        competencia_core: CompetenciaCoreService,
        equipo_core: CompetenciaEquipoCoreService,
        ronda_core: RondaCoreService,
        encuentro_core: EncuentroCoreService,
        auditoria_core: AuditoriaCoreService,
        selector: CompetenciaSelector,
        alcance: IAlcanceEdicion,
        elegibilidad: IEquipoElegibleService,
    ):
        self.competencia_core = competencia_core
        self.equipo_core = equipo_core
        self.ronda_core = ronda_core
        self.encuentro_core = encuentro_core
        self.auditoria_core = auditoria_core
        self.selector = selector
        self.alcance = alcance
        self.elegibilidad = elegibilidad

    # ── Alta de la competencia ──────────────────────────────────────────────

    async def crear_competencia(
        self,
        data: CompetenciaCreateData,
        *,
        actor=None,
    ) -> CompetenciaDetalleResult:
        """Crea la competencia en la edición pedida.

        La EDICIÓN la resuelve el servidor por el orden congelado
        (`FR-02` §2.2): el cliente la declara, pero el servidor la resuelve y
        la comprueba contra el catálogo.
        """
        edicion = await sync_to_async(self._resolver_edicion)(data.edicion_id)
        competencia = await sync_to_async(self._crear_competencia_sync)(
            edicion,
            data,
            actor,
        )
        return await sync_to_async(self.selector.detalle)(competencia.id)

    def _resolver_edicion(self, edicion_id):
        """La edición explícita del alcance."""
        return self.alcance.resolver_explicita(edicion_id)

    @transaction.atomic()
    def _crear_competencia_sync(self, edicion, data, actor):
        """Alta atómica de la competencia y de su acta."""
        competencia = self.competencia_core.crear(edicion, data)
        self.auditoria_core.registrar(
            accion=AccionAuditada.CREACION_COMPETENCIA,
            motivo="Alta de la competencia",
            competencia=competencia,
            actor=actor,
            detalle={"edicion_id": str(edicion.id)},
        )
        return competencia

    # ── Equipos del cuadro ─────────────────────────────────────────────────

    async def incorporar_equipo(
        self,
        competencia_id,
        data: EquipoCompetenciaCreateData,
        *,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Incorpora un equipo al cuadro con su semilla MANUAL.

        La ELEGIBILIDAD la resuelve `modules.salesianos_fest` por el puerto
        `IEquipoElegibleService`: este módulo NO reimplementa ninguna regla de
        inscripción (`RN-K01`, `QA-K01`). El veredicto del puerto trae el
        MOTIVO del rechazo y el dominio lo traduce a una excepción con código
        público.
        """
        competencia = await sync_to_async(self.selector.obtener_por_id)(competencia_id)
        veredicto = await sync_to_async(self._veredicto)(
            data.equipo_id,
            str(competencia.edicion_id),
            str(competencia.disciplina_id),
        )
        participacion = await sync_to_async(self._incorporar_sync)(
            competencia,
            data,
            veredicto,
            actor,
        )
        return await sync_to_async(self._proyectar_equipo)(participacion)

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
        """Edita la semilla o el estado de la participación en el cuadro."""
        participacion = await sync_to_async(self._obtener_participacion)(
            competencia_id,
            participacion_id,
        )
        await sync_to_async(self._editar_equipo_sync)(
            participacion,
            data,
            expected_version,
            motivo,
            actor,
        )
        return await sync_to_async(self._proyectar_equipo)(participacion)

    # ── Rondas y encuentros ─────────────────────────────────────────────────

    async def crear_ronda(
        self,
        competencia_id,
        data: RondaCreateData,
        *,
        actor=None,
    ):
        """Crea una ronda del cuadro."""
        competencia = await sync_to_async(self.selector.obtener_por_id)(competencia_id)
        ronda = await sync_to_async(self._crear_ronda_sync)(competencia, data, actor)
        return await sync_to_async(self._proyectar_ronda)(ronda)

    async def crear_encuentro(
        self,
        competencia_id,
        ronda_id,
        data,
        *,
        actor=None,
    ):
        """Crea un encuentro en la ronda, posiblemente VACÍO."""
        ronda = await sync_to_async(self._obtener_ronda)(competencia_id, ronda_id)
        encuentro = await sync_to_async(self._crear_encuentro_sync)(ronda, data, actor)
        return await sync_to_async(self._proyectar_encuentro)(encuentro)

    # ── internos ───────────────────────────────────────────────────────────

    def _veredicto(self, equipo_id, edicion_id, disciplina_id):
        """El veredicto de ELEGIBILIDAD del puerto (no lanza: decide)."""
        return self.elegibilidad.verificar_elegibilidad(
            equipo_id,
            edicion_id,
            disciplina_id,
        )

    @transaction.atomic()
    def _incorporar_sync(self, competencia, data, veredicto, actor):
        """Alta atómica de la participación y de su acta."""
        participacion = self.equipo_core.incorporar(
            competencia,
            data,
            elegible=bool(veredicto.es_elegible),
            motivo_no_elegibilidad=str(veredicto.motivo),
        )
        self.auditoria_core.registrar(
            accion=AccionAuditada.INCORPORACION_EQUIPO,
            motivo="Alta de equipo en la competencia",
            competencia=competencia,
            actor=actor,
            detalle={"equipo_id": str(data.equipo_id), "orden": data.orden},
        )
        return participacion

    @transaction.atomic()
    def _editar_equipo_sync(
        self,
        participacion,
        data,
        expected_version,
        motivo,
        actor,
    ):
        """Edición atómica de la participación y de su acta."""
        actualizado = self.equipo_core.editar(
            participacion,
            data,
            expected_version=expected_version,
            motivo=motivo,
        )
        self.auditoria_core.registrar(
            accion=AccionAuditada.EDICION_EQUIPO,
            motivo=motivo or "Edición del equipo de la competencia",
            competencia=actualizado.competencia,
            actor=actor,
            detalle={
                "orden": actualizado.orden,
                "estado": actualizado.estado,
            },
        )
        return actualizado

    @transaction.atomic()
    def _crear_ronda_sync(self, competencia, data, actor):
        """Alta atómica de la ronda y de su acta."""
        ronda = self.ronda_core.crear(competencia, data)
        self.auditoria_core.registrar(
            accion=AccionAuditada.CREACION_RONDA,
            motivo="Alta de ronda en el cuadro",
            competencia=competencia,
            actor=actor,
            detalle={"etiqueta": ronda.etiqueta, "orden": ronda.orden},
        )
        return ronda

    @transaction.atomic()
    def _crear_encuentro_sync(self, ronda, data, actor):
        """Alta atómica del encuentro y de su acta."""
        encuentro = self.encuentro_core.crear(ronda, data)
        self.auditoria_core.registrar(
            accion=AccionAuditada.CREACION_ENCUENTRO,
            motivo="Alta de encuentro en la ronda",
            competencia=ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={"orden": encuentro.orden},
        )
        return encuentro

    def _obtener_participacion(self, competencia_id, participacion_id):
        """La participación, comprobando que es de la competencia indicada."""
        from modules.competencias.domain.exceptions import (
            CompetenciaEquipoNoEncontradaError,
        )
        from modules.competencias.domain.models import CompetenciaEquipo

        participacion = (
            CompetenciaEquipo.objects.select_related("equipo", "competencia")
            .filter(id=participacion_id, competencia_id=competencia_id)
            .first()
        )
        if participacion is None:
            raise CompetenciaEquipoNoEncontradaError()
        return participacion

    def _obtener_ronda(self, competencia_id, ronda_id):
        """La ronda, comprobando que es de la competencia indicada."""
        from modules.competencias.domain.exceptions import RondaNoEncontradaError
        from modules.competencias.domain.models import Ronda

        ronda = (
            Ronda.objects.select_related("competencia")
            .filter(id=ronda_id, competencia_id=competencia_id)
            .first()
        )
        if ronda is None:
            raise RondaNoEncontradaError()
        return ronda

    def _proyectar_equipo(self, participacion):
        from modules.competencias.domain.selectors.proyeccion import proyectar_equipo

        return proyectar_equipo(participacion)

    def _proyectar_ronda(self, ronda):
        from modules.competencias.domain.selectors.proyeccion import proyectar_ronda

        return proyectar_ronda(ronda, [])

    def _proyectar_encuentro(self, encuentro):
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        return proyectar_encuentro(encuentro)


__all__ = ["CuadroFlujo"]
