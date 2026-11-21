"""Selectores de `Encuentro`: el cuadro, la agenda y el detalle.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.12

**Una sola fuente operativa.** `FL-11` paso 6 exige que la lista, la agenda
y el bracket compartan una sola fuente de datos. Este selector es esa fuente:
el cuadro, la agenda y el detalle salen de aquí, y los tres proyectan con
`proyeccion.py`. No hay una consulta de agenda y una consulta de cuadro que
puedan discrepar.

**La agenda es TRANSVERSAL** (`frontend/05` §2): reúne los encuentros del día
de TODAS las competencias de la edición, ordenados por hora de inicio.
"""

from datetime import date

from django.db.models import Q

from modules.competencias.domain.constants import (
    ESTADO_PUBLICO_POR_ESTADO,
    EstadoCompetencia,
    EstadoEncuentro,
    EstadoEncuentroPublico,
)
from modules.competencias.domain.exceptions import EncuentroNoEncontradoError
from modules.competencias.domain.models import CompetenciaEquipo, Encuentro, Ronda
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    EncuentroResult,
    EncuentrosPublicosResult,
    MisPartidosResult,
    RondaResult,
)
from modules.competencias.domain.selectors.proyeccion import (
    proyectar_encuentro,
    proyectar_equipo,
    proyectar_ronda,
)


class EncuentroSelector:
    """Lecturas de los encuentros: cuadro, agenda y detalle."""

    # ── consultas ───────────────────────────────────────────────────────────

    def obtener_por_id(self, encuentro_id) -> Encuentro:
        """El encuentro, o el error de no encontrado (404)."""
        try:
            return (
                Encuentro.objects.select_related(
                    "ronda",
                    "ronda__competencia",
                    "participante_1",
                    "participante_1__equipo",
                    "participante_2",
                    "participante_2__equipo",
                    "ganador",
                    "ganador__equipo",
                ).get(id=encuentro_id)
            )
        except (Encuentro.DoesNotExist, ValueError, TypeError):
            raise EncuentroNoEncontradoError()

    def rondas(self, competencia_id) -> list[RondaResult]:
        """El cuadro completo de una competencia: rondas y encuentros.

        Las rondas invalidadas se conservan y se devuelven: el cuadro que se
        trazó con ellas sigue en la historia (`RN-K02`).
        """
        rondas = list(
            Ronda.objects.filter(competencia_id=competencia_id)
            .prefetch_related(
                "encuentros__participante_1__equipo",
                "encuentros__participante_2__equipo",
                "encuentros__ganador__equipo",
            )
            .order_by("orden")
        )
        return [
            proyectar_ronda(ronda, sorted(ronda.encuentros.all(), key=lambda e: e.orden))
            for ronda in rondas
        ]

    def agenda(self, edicion_id, dia: date, edicion_nombre: str = "") -> AgendaResult:
        """Los encuentros programados del día, en el alcance de la edición.

        Un encuentro sin horario NO aparece en la agenda: la agenda es el
        horario, y un encuentro sin horario no tiene lugar en él. Los
        encuentros CANCELADOS se excluyen: no reservan la franja.
        """
        encuentros = list(
            Encuentro.objects.filter(
                ronda__competencia__edicion_id=edicion_id,
                inicio_programado__isnull=False,
                fin_programado__isnull=False,
                inicio_programado__date=dia,
            )
            .exclude(estado="CANCELADO")
            .select_related(
                "ronda",
                "ronda__competencia",
                "participante_1",
                "participante_1__equipo",
                "participante_2",
                "participante_2__equipo",
                "ganador",
                "ganador__equipo",
            )
            .order_by("inicio_programado", "ronda__orden", "orden")
        )
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        return AgendaResult(
            edicion_id=str(edicion_id),
            edicion_nombre=edicion_nombre,
            fecha=dia,
            total=len(encuentros),
            encuentros=[proyectar_encuentro(encuentro) for encuentro in encuentros],
        )

    def publicos(
        self,
        edicion_id,
        edicion_nombre: str = "",
    ) -> EncuentrosPublicosResult:
        """Los encuentros PUBLICABLES de la edición, en sus TRES cubos.

        Lo que se publica es lo que el administrador dejó vivo: la lectura
        pública no filtra por competencia ni inventa datos. NO se publica un
        encuentro `CANCELADO`, ni los encuentros de una competencia `CANCELADA`.

        Los cubos son los de la exploración (`explore` §5.1): lo que está EN
        JUEGO, lo que VIENE y lo que YA TERMINÓ. Cada encuentro se proyecta
        con `proyectar_encuentro`: la superficie pública comparte la forma
        canónica con la agenda, el cuadro y el detalle.
        """
        encuentros = list(
            Encuentro.objects.filter(ronda__competencia__edicion_id=edicion_id)
            .exclude(estado=EstadoEncuentro.CANCELADO)
            .exclude(ronda__competencia__estado=EstadoCompetencia.CANCELADA)
            .select_related(
                "ronda",
                "participante_1",
                "participante_1__equipo",
                "participante_2",
                "participante_2__equipo",
                "ganador",
                "ganador__equipo",
            )
            .order_by("ronda__orden", "orden")
        )
        proyectados = [proyectar_encuentro(encuentro) for encuentro in encuentros]

        cubos: dict[str, list[EncuentroResult]] = {
            EstadoEncuentroPublico.EN_VIVO: [],
            EstadoEncuentroPublico.PROGRAMA: [],
            EstadoEncuentroPublico.FINALIZADO: [],
        }
        for encuentro in proyectados:
            cubo = ESTADO_PUBLICO_POR_ESTADO.get(encuentro.estado)
            if cubo is None:
                # Un estado sin cubo público NO se publica (cancelado).
                continue
            cubos[cubo].append(encuentro)

        en_vivo = _por_inicio(cubos[EstadoEncuentroPublico.EN_VIVO])
        proximos = _por_inicio(cubos[EstadoEncuentroPublico.PROGRAMA])
        finalizados = _por_fin(cubos[EstadoEncuentroPublico.FINALIZADO])

        return EncuentrosPublicosResult(
            edicion_id=str(edicion_id),
            edicion_nombre=edicion_nombre,
            # El total es la SUMA de los cubos: un encuentro sin cubo público
            # no se publica, y el total nunca puede desmentir a los cubos.
            total=len(en_vivo) + len(proximos) + len(finalizados),
            en_vivo=en_vivo,
            proximos=proximos,
            finalizados=finalizados,
        )


    def mis_partidos(self, equipo_ids: list[str]) -> MisPartidosResult:
        """Los partidos de los equipos dados, en sus TRES cubos.

        Son los encuentros en los que el equipo de la cuenta ocupa alguno de
        los dos slots. La consulta es UNA sola ⇒ un encuentro en el que juegan
        DOS equipos de la cuenta aparece UNA vez.

        Una cuenta sin equipos devuelve un resultado VACÍO: no es un error (el
        servidor no tiene nada que publicar sobre ella).
        """
        if not equipo_ids:
            return MisPartidosResult()

        participaciones = list(
            CompetenciaEquipo.objects.filter(equipo_id__in=equipo_ids)
            .select_related("equipo", "competencia", "competencia__edicion")
            .order_by("orden")
        )
        participacion_ids = [participacion.id for participacion in participaciones]

        encuentros = (
            Encuentro.objects.filter(
                Q(participante_1_id__in=participacion_ids)
                | Q(participante_2_id__in=participacion_ids)
            )
            .exclude(estado=EstadoEncuentro.CANCELADO)
            .exclude(ronda__competencia__estado=EstadoCompetencia.CANCELADA)
            .select_related(
                "ronda",
                "participante_1",
                "participante_1__equipo",
                "participante_2",
                "participante_2__equipo",
                "ganador",
                "ganador__equipo",
            )
            .order_by("ronda__orden", "orden")
        )

        en_vivo, proximos, finalizados = _cubos_de(encuentros)
        edicion = participaciones[0].competencia.edicion if participaciones else None

        return MisPartidosResult(
            edicion_id=str(edicion.id) if edicion is not None else "",
            edicion_nombre=edicion.nombre if edicion is not None else "",
            total=len(en_vivo) + len(proximos) + len(finalizados),
            equipos=[
                proyectar_equipo(participacion) for participacion in participaciones
            ],
            en_vivo=en_vivo,
            proximos=proximos,
            finalizados=finalizados,
        )


def _cubos_de(encuentros) -> tuple[list, list, list]:
    """Reparte unos encuentros en sus TRES cubos.

    Los cubos son los mismos que publica la superficie pública: lo que está
    en juego, lo que viene y lo que ya terminó. Un encuentro sin cubo (el
    cancelado) no se publica.
    """
    cubos: dict[str, list[EncuentroResult]] = {
        EstadoEncuentroPublico.EN_VIVO: [],
        EstadoEncuentroPublico.PROGRAMA: [],
        EstadoEncuentroPublico.FINALIZADO: [],
    }
    for encuentro in encuentros:
        proyectado = proyectar_encuentro(encuentro)
        cubo = ESTADO_PUBLICO_POR_ESTADO.get(proyectado.estado)
        if cubo is None:
            continue
        cubos[cubo].append(proyectado)

    return (
        _por_inicio(cubos[EstadoEncuentroPublico.EN_VIVO]),
        _por_inicio(cubos[EstadoEncuentroPublico.PROGRAMA]),
        _por_fin(cubos[EstadoEncuentroPublico.FINALIZADO]),
    )


def _por_inicio(encuentros: list[EncuentroResult]) -> list[EncuentroResult]:
    """Los encuentros más PRÓXIMOS primero: por hora de inicio.

    El encuentro sin horario va AL FINAL: no tiene una hora que lo sitúe.
    """
    return sorted(
        encuentros,
        key=lambda e: (
            e.inicio_programado is None,
            e.inicio_programado,
            e.ronda_orden,
            e.orden,
        ),
    )


def _por_fin(encuentros: list[EncuentroResult]) -> list[EncuentroResult]:
    """Los resultados MÁS RECIENTES primero: por hora de fin."""
    return sorted(
        encuentros,
        key=lambda e: (
            e.finalizado_en is None,
            e.finalizado_en,
            e.ronda_orden,
            e.orden,
        ),
        reverse=True,
    )


__all__ = ["EncuentroSelector"]
