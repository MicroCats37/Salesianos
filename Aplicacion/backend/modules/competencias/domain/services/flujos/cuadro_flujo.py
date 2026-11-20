"""`CuadroFlujo` — el ALTA de la estructura del cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.

Alcance de este flujo:

- alta de la **competencia** (con su edición, su disciplina y su categoría
  resueltas por el servidor);
- **incorporación** de un equipo elegible (la elegibilidad la decide el
  dueño de la inscripción y aquí se CONSUME por el puerto, `RN-K01`);
- **edición** de la participación (semilla manual y retirada);
- alta de **rondas** y de **encuentros**.

La actualización de un encuentro (participantes, horario, bye, enlace y
estado) vive en `EncuentroFlujo`: son comandos distintos, con reglas
distintas.
"""

from math import log2

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from injector import inject

from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.constants import EstadoCompetenciaEquipo, EstadoEncuentro, SlotDestino
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
            str(competencia.categoria_id),
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

    async def generar_cuadro(self, competencia_id, *, actor=None):
        """Genera una llave de eliminación simple desde las semillas activas."""
        await sync_to_async(self._generar_cuadro_sync)(competencia_id, actor)
        return await sync_to_async(self.selector.detalle)(competencia_id)

    # ── internos ───────────────────────────────────────────────────────────

    def _veredicto(self, equipo_id, edicion_id, disciplina_id, categoria_id):
        """El veredicto de ELEGIBILIDAD del puerto (no lanza: decide)."""
        return self.elegibilidad.verificar_elegibilidad(
            equipo_id,
            edicion_id,
            disciplina_id,
            categoria_id,
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

    @transaction.atomic()
    def _generar_cuadro_sync(self, competencia_id, actor):
        """Persiste en una única transacción la llave inicial y sus enlaces."""
        from modules.competencias.domain.exceptions import TransicionInvalidaError
        from modules.competencias.domain.models import Competencia, CompetenciaEquipo, Encuentro, Ronda

        competencia_base = self.selector.obtener_por_id(competencia_id)
        competencia = Competencia.objects.select_for_update().get(id=competencia_base.id)
        if Ronda.objects.filter(competencia=competencia).exists():
            raise TransicionInvalidaError()

        equipos = list(
            CompetenciaEquipo.objects.select_for_update()
            .filter(competencia=competencia, estado=EstadoCompetenciaEquipo.ACTIVO)
            .order_by("orden")
        )
        if len(equipos) < 2:
            raise TransicionInvalidaError()

        tamano_llave = 1 << (len(equipos) - 1).bit_length()
        total_rondas = int(log2(tamano_llave))
        rondas = []
        encuentros_por_ronda = []

        for indice_ronda in range(total_rondas):
            encuentros_en_ronda = tamano_llave >> (indice_ronda + 1)
            ronda = Ronda.objects.create(
                competencia=competencia,
                etiqueta=self._etiqueta_ronda(encuentros_en_ronda),
                orden=indice_ronda + 1,
            )
            rondas.append(ronda)
            encuentros = []
            for indice_encuentro in range(encuentros_en_ronda):
                participante_1 = None
                participante_2 = None
                if indice_ronda == 0:
                    siembras = self._orden_siembra(tamano_llave)
                    posicion = indice_encuentro * 2
                    semilla_1 = siembras[posicion]
                    semilla_2 = siembras[posicion + 1]
                    participante_1 = equipos[semilla_1 - 1] if semilla_1 <= len(equipos) else None
                    participante_2 = equipos[semilla_2 - 1] if semilla_2 <= len(equipos) else None

                es_bye = (participante_1 is None) != (participante_2 is None)
                ganador = (participante_1 or participante_2) if es_bye else None
                encuentros.append(
                    Encuentro.objects.create(
                        ronda=ronda,
                        orden=indice_encuentro + 1,
                        participante_1=participante_1,
                        participante_2=participante_2,
                        es_bye=es_bye,
                        ganador=ganador,
                        estado=(EstadoEncuentro.FINALIZADO if es_bye else EstadoEncuentro.BORRADOR),
                        finalizado_en=timezone.now() if es_bye else None,
                    )
                )
            encuentros_por_ronda.append(encuentros)

        for indice_ronda, encuentros in enumerate(encuentros_por_ronda[:-1]):
            destinos = encuentros_por_ronda[indice_ronda + 1]
            for indice, encuentro in enumerate(encuentros):
                encuentro.siguiente_encuentro = destinos[indice // 2]
                encuentro.slot_destino = (
                    SlotDestino.PARTICIPANTE_1
                    if indice % 2 == 0
                    else SlotDestino.PARTICIPANTE_2
                )
                encuentro.save(update_fields=["siguiente_encuentro", "slot_destino", "updated_at"])

        # A bye is already resolved at generation time, so its winner must occupy
        # the successor slot before an administrator starts operating the bracket.
        for encuentro in encuentros_por_ronda[0]:
            if not encuentro.es_bye:
                continue
            campo_destino = (
                "participante_1"
                if encuentro.slot_destino == SlotDestino.PARTICIPANTE_1
                else "participante_2"
            )
            setattr(encuentro.siguiente_encuentro, campo_destino, encuentro.ganador)
            encuentro.siguiente_encuentro.save(
                update_fields=[campo_destino, "updated_at"]
            )

        self.auditoria_core.registrar(
            accion=AccionAuditada.CREACION_ENCUENTRO,
            motivo="Generación inicial del cuadro de eliminación simple",
            competencia=competencia,
            actor=actor,
            detalle={
                "equipos_activos": len(equipos),
                "tamano_llave": tamano_llave,
                "rondas": len(rondas),
                "encuentros": sum(len(encuentros) for encuentros in encuentros_por_ronda),
            },
        )

    @staticmethod
    def _etiqueta_ronda(encuentros: int) -> str:
        etiquetas = {1: "Final", 2: "Semifinales", 4: "Cuartos de final", 8: "Octavos de final"}
        return etiquetas.get(encuentros, f"Ronda de {encuentros * 2}")

    @staticmethod
    def _orden_siembra(tamano_llave: int) -> list[int]:
        """Distribuye las semillas para que las más altas reciban los byes."""
        siembras = [1, 2]
        while len(siembras) < tamano_llave:
            siguiente_tamano = len(siembras) * 2 + 1
            siembras = [
                semilla
                for semilla in siembras
                for semilla in (semilla, siguiente_tamano - semilla)
            ]
        return siembras

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
