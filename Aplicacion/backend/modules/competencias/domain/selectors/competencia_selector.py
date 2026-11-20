"""Selectores de `Competencia` y de la participación de sus equipos.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.12 ·
          `contract/api-wrapper-presenter-contract.md` §3

Un selector CARGA y PROYECTA. No decide nada: las reglas viven en los
servicios core. Sus consultas son de alcance de EDICIÓN (`RN-E01`): una
competencia sin edición no existe y no se puede leer.
"""

from django.db.models import Count, Q

from modules.competencias.domain.exceptions import CompetenciaNoEncontradaError
from modules.competencias.domain.models import Competencia, CompetenciaEquipo
from modules.competencias.domain.results.competencias_results import (
    CompetenciaDetalleResult,
    CompetenciaListadoResult,
)
from modules.competencias.domain.selectors.proyeccion import proyectar_equipo


class CompetenciaSelector:
    """Lecturas de las competencias de una edición y de sus equipos."""

    # ── consultas ───────────────────────────────────────────────────────────

    def listar(
        self,
        edicion_id,
        *,
        disciplina_id=None,
        categoria_id=None,
        estado=None,
    ) -> list[CompetenciaListadoResult]:
        """Las competencias de la edición, con sus tres contadores.

        Los contadores los calcula la BASE DE DATOS con un número constante de
        consultas: el cliente nunca los re-deriva (`RN-A02`).

        El filtro por CATEGORÍA es el que permite recorrer los cuadros por
        franja etaria: es la PARIDAD con el filtro público histórico
        `GET /competencias?categoria_id=`.
        """
        consultas = Competencia.objects.filter(edicion_id=edicion_id)
        if disciplina_id:
            consultas = consultas.filter(disciplina_id=disciplina_id)
        if categoria_id:
            consultas = consultas.filter(categoria_id=categoria_id)
        if estado:
            consultas = consultas.filter(estado=estado)

        filas = (
            consultas.select_related("disciplina", "categoria")
            .annotate(
                total_equipos=Count(
                    "equipos",
                    filter=Q(equipos__estado="ACTIVO"),
                    distinct=True,
                ),
                total_encuentros=Count(
                    "rondas__encuentros",
                    distinct=True,
                ),
                total_encuentros_finalizados=Count(
                    "rondas__encuentros",
                    filter=Q(rondas__encuentros__estado="FINALIZADO"),
                    distinct=True,
                ),
            )
            .order_by("-fecha", "nombre")
        )
        return [
            CompetenciaListadoResult(
                id=str(competencia.id),
                edicion_id=str(competencia.edicion_id),
                disciplina_id=str(competencia.disciplina_id),
                disciplina_nombre=competencia.disciplina.nombre,
                categoria_id=str(competencia.categoria_id),
                categoria_nombre=competencia.categoria.nombre,
                nombre=competencia.nombre,
                estado=competencia.estado,
                fecha=competencia.fecha,
                total_equipos=competencia.total_equipos,
                total_encuentros=competencia.total_encuentros,
                total_encuentros_finalizados=competencia.total_encuentros_finalizados,
            )
            for competencia in filas
        ]

    def obtener_por_id(self, competencia_id) -> Competencia:
        """La competencia, o el error de no encontrada (404).

        Es el LECTOR del servicio core: el servicio y el flujo lo usan para
        resolver la entidad antes de operar sobre ella.
        """
        try:
            return Competencia.objects.select_related(
                "edicion",
                "disciplina",
                "categoria",
            ).get(id=competencia_id)
        except (Competencia.DoesNotExist, ValueError, TypeError):
            raise CompetenciaNoEncontradaError()

    def equipos(self, competencia_id) -> list:
        """Las participaciones de los equipos de la competencia, en orden."""
        return list(
            CompetenciaEquipo.objects.filter(competencia_id=competencia_id)
            .select_related("equipo")
            .order_by("orden")
        )

    def detalle(self, competencia_id) -> CompetenciaDetalleResult:
        """El detalle operativo de la competencia.

        Reúne los equipos y el cuadro completo. Es la MISMA fuente que
        consumen el cuadro y la agenda (`FL-11` paso 6).
        """
        competencia = self.obtener_por_id(competencia_id)
        from modules.competencias.domain.selectors.encuentro_selector import (
            EncuentroSelector,
        )

        rondas = EncuentroSelector().rondas(competencia.id)
        return CompetenciaDetalleResult(
            id=str(competencia.id),
            edicion_id=str(competencia.edicion_id),
            edicion_nombre=competencia.edicion.nombre,
            disciplina_id=str(competencia.disciplina_id),
            disciplina_nombre=competencia.disciplina.nombre,
            categoria_id=str(competencia.categoria_id),
            categoria_nombre=competencia.categoria.nombre,
            nombre=competencia.nombre,
            estado=competencia.estado,
            fecha=competencia.fecha,
            version=competencia.version,
            equipos=[proyectar_equipo(equipo) for equipo in self.equipos(competencia.id)],
            rondas=rondas,
        )

    def proyectar_equipos(self, competencia_id) -> list:
        """Las participaciones ya proyectadas a `CompetenciaEquipoResult`."""
        return [proyectar_equipo(equipo) for equipo in self.equipos(competencia_id)]

    def proyectar_rondas(self, competencia_id) -> list:
        """Las rondas ya proyectadas a `RondaResult`."""
        from modules.competencias.domain.selectors.encuentro_selector import (
            EncuentroSelector,
        )

        return EncuentroSelector().rondas(competencia_id)


__all__ = ["CompetenciaSelector"]
