"""
CompetenciaSelector — read-only queries of the competitions of the bracket.

The selector loads the relations and returns DOMAIN RESULT DTOs (never HTTP
schemas): the presenter of the presentation layer maps them
(`contract/api-wrapper-presenter-contract.md` §3).

Two invariants of this selector:

1. **Constant number of queries.** The counters of the list are computed
   with aggregate queries over the whole filtered set, never with a Python
   loop over a queryset.
2. **The scope is applied by the server.** `eventos_permitidos` restricts the
   result to the events the reader is authorized for; `None` means "no
   restriction" (the administrative surface).

Read-only by construction: no method in this selector writes.
"""
from django.db.models import Count, Q

from modules.competencias.domain.constants import (
    EstadoCompetenciaEquipoChoices,
    EstadoEncuentroChoices,
)
from modules.competencias.domain.models import Competencia, CompetenciaEquipo
from modules.competencias.domain.models import Encuentro, Ronda
from modules.competencias.domain.results.competencias_results import (
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
    CompetenciaListadoResult,
    CompetenciaResult,
    CuadroResult,
    EncuentroResult,
    RondaCuadroResult,
    RondaResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaFiltrosData,
)


class CompetenciaSelector:
    """Read-only queries of `Competencia` and of its bracket."""

    # ── list ───────────────────────────────────────────────────────────────

    def listar(
        self,
        filtros: CompetenciaFiltrosData | None = None,
        eventos_permitidos: list[str] | None = None,
    ) -> list[CompetenciaListadoResult]:
        """Return the competitions of the scope, with their counters.

        The filters combine with AND. `eventos_permitidos=None` means "every
        edition" (the administrative surface); an empty list means "no
        edition is authorized" and the result is empty.
        """
        filtros = filtros or CompetenciaFiltrosData()
        qs = Competencia.objects.select_related("evento", "disciplina", "categoria")
        qs = self._aplicar_filtros(qs, filtros)
        qs = self._aplicar_alcance(qs, eventos_permitidos)
        competencias = list(qs.order_by("fecha", "nombre", "created_at"))

        contadores = self._contadores([c.id for c in competencias])

        resultados = []
        for competencia in competencias:
            conteo = contadores.get(str(competencia.id), {})
            resultados.append(
                CompetenciaListadoResult(
                    **CompetenciaResult.desde(competencia).model_dump(),
                    total_equipos=conteo.get("equipos", 0),
                    total_encuentros=conteo.get("encuentros", 0),
                    total_encuentros_finalizados=conteo.get("finalizados", 0),
                )
            )
        return resultados

    # ── detail ─────────────────────────────────────────────────────────────

    def obtener_detalle(
        self,
        competencia_id,
        eventos_permitidos: list[str] | None = None,
    ) -> CompetenciaDetalleResult | None:
        """Return the competition with its teams and its rounds.

        Returns None when the competition does not exist OR when it is
        outside of the authorized scope: the surface must never confirm the
        existence of a resource the reader cannot see.
        """
        competencia = self._obtener(competencia_id, eventos_permitidos)
        if competencia is None:
            return None

        contadores = self._contadores([competencia.id])
        conteo = contadores.get(str(competencia.id), {})

        return CompetenciaDetalleResult(
            **CompetenciaResult.desde(competencia).model_dump(),
            total_equipos=conteo.get("equipos", 0),
            total_encuentros=conteo.get("encuentros", 0),
            total_encuentros_finalizados=conteo.get("finalizados", 0),
            equipos=self.listar_equipos(competencia.id),
            rondas=self.listar_rondas(competencia.id),
        )

    # ── teams and rounds ───────────────────────────────────────────────────

    def listar_equipos(self, competencia_id) -> list[CompetenciaEquipoResult]:
        """Return the teams registered in the bracket, in their manual order."""
        entradas = (
            CompetenciaEquipo.objects.filter(competencia_id=competencia_id)
            .select_related("equipo")
            .order_by("orden", "created_at")
        )
        return [CompetenciaEquipoResult.desde(entrada) for entrada in entradas]

    def listar_rondas(self, competencia_id) -> list[RondaResult]:
        """Return the rounds of the bracket, in their order."""
        rondas = list(
            Ronda.objects.filter(competencia_id=competencia_id).order_by(
                "orden", "created_at"
            )
        )
        conteos = {
            fila["ronda_id"]: fila["cantidad"]
            for fila in Encuentro.objects.filter(ronda__competencia_id=competencia_id)
            .values("ronda_id")
            .annotate(cantidad=Count("id"))
        }
        resultados = []
        for ronda in rondas:
            resultado = RondaResult.desde(ronda)
            resultado.total_encuentros = conteos.get(ronda.id, 0)
            resultados.append(resultado)
        return resultados

    # ── bracket ────────────────────────────────────────────────────────────

    def obtener_cuadro(
        self,
        competencia_id,
        eventos_permitidos: list[str] | None = None,
    ) -> CuadroResult | None:
        """Return the bracket of the competition.

        An EMPTY or PARTIAL bracket is a valid bracket: the rounds and the
        encounters that exist are returned as they are and NOTHING is
        invented (spec: "un cuadro vacío o parcial MUST ser legible y
        editable sin inventar participantes ni avances").
        """
        competencia = self._obtener(competencia_id, eventos_permitidos)
        if competencia is None:
            return None

        rondas = list(
            Ronda.objects.filter(competencia_id=competencia.id).order_by(
                "orden", "created_at"
            )
        )
        encuentros = list(
            Encuentro.objects.filter(ronda__competencia_id=competencia.id)
            .select_related(
                "ronda__competencia",
                "participante_1__equipo",
                "participante_2__equipo",
            )
            .order_by("ronda__orden", "orden")
        )

        por_ronda: dict[str, list[EncuentroResult]] = {}
        for encuentro in encuentros:
            por_ronda.setdefault(str(encuentro.ronda_id), []).append(
                EncuentroResult.desde(encuentro)
            )

        columnas = []
        for ronda in rondas:
            columnas.append(
                RondaCuadroResult(
                    id=str(ronda.id),
                    etiqueta=ronda.etiqueta,
                    orden=ronda.orden,
                    estado=ronda.estado,
                    encuentros=por_ronda.get(str(ronda.id), []),
                )
            )

        contadores = self._contadores([competencia.id])
        conteo = contadores.get(str(competencia.id), {})

        return CuadroResult(
            competencia_id=str(competencia.id),
            nombre=competencia.nombre,
            fecha=competencia.fecha,
            estado=competencia.estado,
            total_equipos=conteo.get("equipos", 0),
            rondas=columnas,
        )

    # ── internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _aplicar_alcance(qs, eventos_permitidos: list[str] | None):
        """Restrict the query to the events the reader is authorized for."""
        if eventos_permitidos is None:
            return qs
        return qs.filter(evento_id__in=eventos_permitidos)

    @staticmethod
    def _aplicar_filtros(qs, filtros: CompetenciaFiltrosData):
        """Apply the filters of the read surface (they combine with AND)."""
        if filtros.evento_id:
            qs = qs.filter(evento_id=filtros.evento_id)
        if filtros.disciplina_id:
            qs = qs.filter(disciplina_id=filtros.disciplina_id)
        if filtros.categoria_id:
            qs = qs.filter(categoria_id=filtros.categoria_id)
        if filtros.estado:
            qs = qs.filter(estado=filtros.estado)
        if filtros.fecha_desde:
            qs = qs.filter(fecha__gte=filtros.fecha_desde)
        if filtros.fecha_hasta:
            qs = qs.filter(fecha__lte=filtros.fecha_hasta)
        return qs

    @classmethod
    def _obtener(
        cls,
        competencia_id,
        eventos_permitidos: list[str] | None = None,
    ) -> Competencia | None:
        """Return the competition inside the scope, or None."""
        qs = Competencia.objects.select_related("evento", "disciplina", "categoria")
        qs = cls._aplicar_alcance(qs, eventos_permitidos)
        try:
            return qs.filter(id=competencia_id).first()
        except (ValueError, TypeError):
            # An id that is not a UUID is simply "not found".
            return None

    @staticmethod
    def _contadores(competencia_ids: list) -> dict:
        """Return the counters of a set of competitions with TWO queries.

        The counters are aggregated over the whole set (never one query per
        competition), so the number of queries does not grow with the size of
        the bracket.
        """
        if not competencia_ids:
            return {}

        equipos = {
            str(fila["competencia_id"]): fila["cantidad"]
            for fila in CompetenciaEquipo.objects.filter(
                competencia_id__in=competencia_ids,
                estado=EstadoCompetenciaEquipoChoices.ACTIVO,
            )
            .values("competencia_id")
            .annotate(cantidad=Count("id"))
        }

        encuentros = {
            str(fila["ronda__competencia_id"]): {
                "encuentros": fila["cantidad"],
                "finalizados": fila["finalizados"],
            }
            for fila in Encuentro.objects.filter(
                ronda__competencia_id__in=competencia_ids
            )
            .values("ronda__competencia_id")
            .annotate(
                cantidad=Count("id"),
                finalizados=Count(
                    "id",
                    filter=Q(estado=EstadoEncuentroChoices.FINALIZADO),
                ),
            )
        }

        contadores: dict = {}
        for competencia_id in competencia_ids:
            clave = str(competencia_id)
            conteo_encuentros = encuentros.get(clave, {})
            contadores[clave] = {
                "equipos": equipos.get(clave, 0),
                "encuentros": conteo_encuentros.get("encuentros", 0),
                "finalizados": conteo_encuentros.get("finalizados", 0),
            }
        return contadores


__all__ = ["CompetenciaSelector"]
