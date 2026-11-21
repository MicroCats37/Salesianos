"""Transactional commands for the live reference tournament."""

from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from modules.competencias.domain.models import EquipoTorneo, GrupoTorneo, PartidoTorneo
from modules.competencias.realtime.publisher import publicar_encuentro_actualizado


class TorneoFlujo:
    """Owns tournament writes; HTTP controllers only map and delegate."""

    @staticmethod
    def _aplicar_campos(partido, data):
        partido.local_id = data.home_id
        partido.visitante_id = data.away_id
        partido.puntaje_local = data.home_score
        partido.puntaje_visitante = data.away_score
        partido.programado_en = data.scheduled_at
        partido.cancha = data.court
        partido.duracion_minutos = data.duration_minutes
        partido.penales_local = data.home_penalties
        partido.penales_visitante = data.away_penalties

    def guardar_grupo(self, group_id, payload):
        with transaction.atomic():
            group = GrupoTorneo.objects.select_for_update().filter(id=group_id).first()
            if group is None:
                raise HttpError(404, "Grupo no encontrado")
            if group.revision != payload.revision:
                raise HttpError(409, "Este grupo cambió. Recarga antes de guardar")

            matches = {
                match.id: match for match in PartidoTorneo.objects.filter(grupo=group)
            }
            if set(matches) != {item.id for item in payload.matches}:
                raise HttpError(422, "Envía todos los partidos del grupo")

            allowed = set(
                EquipoTorneo.objects.filter(grupo=group).values_list("id", flat=True)
            )
            for item in payload.matches:
                if (
                    item.home_id not in allowed
                    or item.away_id not in allowed
                    or item.home_id == item.away_id
                ):
                    raise HttpError(422, f"Revisa los rivales del partido {item.id}")
                self._aplicar_campos(matches[item.id], item)
                matches[item.id].save()

            group.revision += 1
            group.save(update_fields=["revision"])
            transaction.on_commit(lambda: publicar_encuentro_actualizado(group.id))
            return {"saved": True, "revision": group.revision}

    def guardar_llave(self, match_id, payload):
        with transaction.atomic():
            partido = (
                PartidoTorneo.objects.select_for_update()
                .filter(id=match_id, grupo__isnull=True)
                .first()
            )
            if partido is None:
                raise HttpError(404, "Partido no encontrado")
            self._aplicar_campos(partido, payload)
            partido.save()
            transaction.on_commit(lambda: publicar_encuentro_actualizado(partido.id))
            return {"saved": True}

    @staticmethod
    def _pausar_reloj(partido, ahora):
        if partido.ejecutando_desde:
            partido.segundos_transcurridos += max(
                0,
                int((ahora - partido.ejecutando_desde).total_seconds()),
            )
            partido.ejecutando_desde = None

    @staticmethod
    def _propagar(partido):
        stages = ("round16", "quarter", "semi", "final")
        if partido.etapa not in stages or partido.etapa == "final":
            return

        next_match = PartidoTorneo.objects.filter(
            competencia=partido.competencia,
            etapa=stages[stages.index(partido.etapa) + 1],
            posicion=partido.posicion // 2,
        ).first()
        if next_match is None:
            return
        if partido.posicion % 2 == 0:
            next_match.local_id = partido.ganador_id
        else:
            next_match.visitante_id = partido.ganador_id
        next_match.save()

    def controlar_partido(self, match_id, payload):
        with transaction.atomic():
            partido = PartidoTorneo.objects.select_for_update().filter(id=match_id).first()
            if partido is None:
                raise HttpError(404, "Partido no encontrado")

            ahora = timezone.now()
            action = payload.action
            if action == "start":
                partido.estado = "live"
                partido.ejecutando_desde = ahora
            elif action == "halftime":
                self._pausar_reloj(partido, ahora)
                partido.estado = "halftime"
            elif action == "resume":
                partido.estado = "live"
                partido.ejecutando_desde = ahora
            elif action == "extra":
                partido.estado = "extra"
                partido.segmento = "extra"
                partido.ejecutando_desde = partido.ejecutando_desde or ahora
            elif action == "penalties":
                self._pausar_reloj(partido, ahora)
                partido.estado = "penalties"
                partido.segmento = "penalties"
            elif action == "reopen":
                partido.estado = "scheduled"
                partido.ganador = None
                partido.decision = None
                partido.ejecutando_desde = None
            elif action == "finish":
                self._pausar_reloj(partido, ahora)
                if payload.decision == "manual":
                    partido.ganador_id = payload.winner_id
                elif payload.decision == "penalties":
                    if partido.penales_local == partido.penales_visitante:
                        raise HttpError(422, "Los penales deben definir un ganador")
                    partido.ganador_id = (
                        partido.local_id
                        if partido.penales_local > partido.penales_visitante
                        else partido.visitante_id
                    )
                elif partido.puntaje_local != partido.puntaje_visitante:
                    partido.ganador_id = (
                        partido.local_id
                        if partido.puntaje_local > partido.puntaje_visitante
                        else partido.visitante_id
                    )
                elif partido.grupo_id is None:
                    raise HttpError(422, "La llave debe tener un ganador")
                partido.decision = payload.decision or (
                    "draw" if partido.ganador_id is None else "score"
                )
                partido.estado = "final"
                self._propagar(partido)
            else:
                raise HttpError(422, "Acción no válida")

            partido.save()
            transaction.on_commit(lambda: publicar_encuentro_actualizado(partido.id))
            return {"saved": True, "status": partido.estado}


__all__ = ["TorneoFlujo"]
