"""`CompetenciasPublicoController` — la superficie PÚBLICA de los encuentros.

Change: `partidos-marcadores-competencias` · Batch 1

| Ruta | Método | Wrapper |
|---|---|---|
| `GET /api/publico/competencias/encuentros` | GET | `EncuentrosPublicosOut` |

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al orquestador
y devuelve el éxito formateado por el presenter. Los errores los traduce el
catálogo global de `core/exceptions.py`; este archivo no construye respuestas
de error.

**La ruta es ANÓNIMA**: `auth=None` + `permissions=[AllowAny]`. El espectador
no tiene sesión: el estado de un encuentro publicado no es un dato reservado.

**La superficie es de SOLO LECTURA.** Publicar un encuentro no es escribirlo:
esta ruta no registra ningún comando, no audita y no muta nada.

**El prefijo NO cuelga de `/api/competencias/`**: esa superficie exige
capacidad administrativa (`SUPERFICIES_CON_CAPACIDAD`, en la frontera de
permisos) y una lectura pública no puede vivir debajo de ella.
"""

from asgiref.sync import sync_to_async
from django.utils import timezone
from injector import inject
from ninja import Schema
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from ninja_jwt.authentication import JWTAuth

from core.permissions import RequireCompetenciasEscribir
from core.responses import ApiResponse, success_response
from modules.competencias.domain.services.orchestrators.competencias_orchestrator import (
    CompetenciasOrchestrator,
)
from modules.competencias.domain.services.flujos import TorneoFlujo
from modules.competencias.presentation.presenters.competencias_publico_presenter import (
    CompetenciasPublicoPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    EncuentrosPublicosOut,
)
from modules.competencias.domain.models import Competencia, EquipoTorneo, GrupoTorneo, PartidoTorneo


def _standings(teams, matches):
    rows = {team.id: {"id": team.id, "name": _team_name(team), "pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0, "dg": 0, "pts": 0} for team in teams}
    for match in matches:
        if match.estado != "final" or match.puntaje_local is None or match.puntaje_visitante is None:
            continue
        home, away = rows[match.local_id], rows[match.visitante_id]
        home["pj"] += 1
        away["pj"] += 1
        home["gf"] += match.puntaje_local
        home["gc"] += match.puntaje_visitante
        away["gf"] += match.puntaje_visitante
        away["gc"] += match.puntaje_local
        if match.puntaje_local > match.puntaje_visitante:
            home["g"] += 1
            away["p"] += 1
            home["pts"] += 3
        elif match.puntaje_local < match.puntaje_visitante:
            away["g"] += 1
            home["p"] += 1
            away["pts"] += 3
        else:
            home["e"] += 1
            away["e"] += 1
            home["pts"] += 1
            away["pts"] += 1
    for row in rows.values():
        row["dg"] = row["gf"] - row["gc"]
    return sorted(rows.values(), key=lambda row: (-row["pts"], -row["dg"], -row["gf"], row["name"]))


def _team_name(team):
    return team.equipo.nombre if team.equipo_id else f"Equipo pendiente ({team.id})"


def _match_out(match, names):
    home_score = match.puntaje_local
    away_score = match.puntaje_visitante
    live_points = {"home": 0, "away": 0}
    if home_score is not None and away_score is not None:
        live_points = {"home": 3, "away": 0} if home_score > away_score else ({"home": 0, "away": 3} if home_score < away_score else {"home": 1, "away": 1})
    elapsed = match.segundos_transcurridos
    if match.ejecutando_desde:
        elapsed += max(0, int((timezone.now() - match.ejecutando_desde).total_seconds()))
    return {
        "id": match.id,
        "group_id": match.grupo_id,
        "stage": match.etapa,
        "category": match.categoria_fixture,
        "title": match.titulo_fixture,
        "position": match.posicion,
        "home_id": match.local_id,
        "away_id": match.visitante_id,
        "home_name": names.get(match.local_id)
        or match.etiqueta_local
        or "Por definir",
        "away_name": names.get(match.visitante_id)
        or match.etiqueta_visitante
        or "Por definir",
        "scheduled_at": (
            match.programado_en.isoformat() if match.programado_en else None
        ),
        "court": match.cancha,
        "duration_minutes": match.duracion_minutos,
        "status": match.estado,
        "home_score": home_score,
        "away_score": away_score,
        "home_penalties": match.penales_local,
        "away_penalties": match.penales_visitante,
        "winner_id": match.ganador_id,
        "decision": match.decision,
        "elapsed_seconds": elapsed,
        "running": match.ejecutando_desde is not None,
        "segment": match.segmento,
        "live_points": live_points,
    }


def _competencias_torneo():
    return list(
        Competencia.objects.filter(
            edicion__estado="PUBLICADA", grupos_torneo__isnull=False
        )
        .select_related("edicion", "disciplina", "categoria")
        .distinct()
        .order_by("fecha", "nombre")
    )


def _estado_torneo(competition_id=None):
    competitions = _competencias_torneo()
    selected_id = str(competition_id) if competition_id else None
    if selected_id is None:
        competition = next(
            (
                item
                for item in competitions
                if item.disciplina.slug == "futbol-7-masculino"
            ),
            competitions[0] if competitions else None,
        )
    else:
        competition = next(
            (item for item in competitions if str(item.id) == selected_id),
            None,
        )
    competition_options = [
        {
            "id": str(item.id),
            "name": item.nombre,
            "discipline": item.disciplina.nombre,
            "category": item.categoria.nombre,
            "date": item.fecha.isoformat(),
        }
        for item in competitions
    ]
    if competition is None:
        return {
            "ready": False,
            "server_time": timezone.now().isoformat(),
            "competitions": competition_options,
            "groups": [],
            "knockout": [],
            "teams": [],
        }
    groups = list(GrupoTorneo.objects.filter(competencia=competition).order_by("id"))
    teams = list(
        EquipoTorneo.objects.filter(competencia=competition).select_related(
            "equipo",
            "equipo__inscripcion__promocion",
        )
    )
    matches = list(PartidoTorneo.objects.filter(competencia=competition).select_related("grupo"))
    names = {team.id: _team_name(team) for team in teams}
    group_data = []
    for group in groups:
        members = [team for team in teams if team.grupo_id == group.id]
        games = sorted([match for match in matches if match.grupo_id == group.id], key=lambda match: (match.programado_en or timezone.now(), match.id))
        group_data.append({"id": group.id, "label": group.etiqueta or group.id, "revision": group.revision, "teams": [{"id": team.id, "name": _team_name(team), "group_id": group.id} for team in sorted(members, key=_team_name)], "table": _standings(members, games), "matches": [_match_out(match, names) for match in games]})
    stage_order = {"round16": 0, "quarter": 1, "semi": 2, "cross": 3, "final": 4, "third_place": 5}
    knockout = [_match_out(match, names) for match in matches if match.grupo_id is None]
    knockout.sort(key=lambda match: (stage_order.get(match["stage"], 9), match["position"]))
    return {
        "ready": True,
        "competition_id": str(competition.id),
        "competition_name": competition.nombre,
        "competitions": competition_options,
        "tournament": competition.edicion.nombre,
        "discipline": competition.disciplina.nombre,
        "category": competition.categoria.nombre,
        "date": competition.fecha.isoformat(),
        "server_time": timezone.now().isoformat(),
        "groups": group_data,
        "knockout": knockout,
        "teams": [
            {"id": team.id, "name": _team_name(team), "group_id": team.grupo_id}
            for team in teams
        ],
    }


class PartidoEdicionIn(Schema):
    id: str
    home_id: str | None = None
    away_id: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    scheduled_at: str | None = None
    court: str | None = None
    duration_minutes: int = 30
    home_penalties: int | None = None
    away_penalties: int | None = None


class GrupoEdicionIn(Schema):
    revision: int
    matches: list[PartidoEdicionIn]


class ControlPartidoIn(Schema):
    action: str
    winner_id: str | None = None
    decision: str | None = None


@api_controller("/publico/competencias", tags=["Competencias públicas"])
class CompetenciasPublicoController:
    """La lectura pública de los encuentros de la edición publicada."""

    @inject
    def __init__(self, orchestrator: CompetenciasOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/encuentros",
        response={200: ApiResponse[EncuentrosPublicosOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Los encuentros publicables de la edición, en sus tres cubos.",
    )
    async def listar_encuentros(self, request):
        """Route: GET /api/publico/competencias/encuentros

        Lo que está EN JUEGO, lo que VIENE y lo que YA TERMINÓ. La edición la
        resuelve el servidor: el navegador no la elige. Si el comité todavía
        no publicó encuentros, la respuesta es una lista VACÍA —no un error—
        porque no hay nada que mostrar todavía.
        """
        resultado = await self.orchestrator.obtener_encuentros_publicos()
        return success_response(CompetenciasPublicoPresenter.present_encuentros(resultado))

    @route.get(
        "/estado",
        response={200: ApiResponse[dict]},
        auth=None,
        permissions=[AllowAny],
    )
    async def estado_torneo(self, request, competition_id: str | None = None):
        return success_response(
            await sync_to_async(_estado_torneo)(competition_id),
        )


__all__ = ["CompetenciasPublicoController"]


@api_controller("/torneo-admin", tags=["Administración del torneo"])
class TorneoAdminController:
    def __init__(self):
        self._torneo = TorneoFlujo()

    @route.put("/groups/{group_id}", response={200: ApiResponse[dict]}, auth=JWTAuth(), permissions=[RequireCompetenciasEscribir])
    async def guardar_grupo(self, request, group_id: str, payload: GrupoEdicionIn):
        return success_response(
            await sync_to_async(self._torneo.guardar_grupo)(group_id, payload),
            message="El grupo se actualizó correctamente.",
        )

    @route.put("/knockout/{match_id}", response={200: ApiResponse[dict]}, auth=JWTAuth(), permissions=[RequireCompetenciasEscribir])
    async def guardar_llave(self, request, match_id: str, payload: PartidoEdicionIn):
        return success_response(
            await sync_to_async(self._torneo.guardar_llave)(match_id, payload),
            message="El partido se actualizó correctamente.",
        )

    @route.post("/matches/{match_id}/control", response={200: ApiResponse[dict]}, auth=JWTAuth(), permissions=[RequireCompetenciasEscribir])
    async def controlar(self, request, match_id: str, payload: ControlPartidoIn):
        return success_response(
            await sync_to_async(self._torneo.controlar_partido)(match_id, payload),
            message="El estado del partido se actualizó correctamente.",
        )


__all__ = ["CompetenciasPublicoController", "TorneoAdminController"]
