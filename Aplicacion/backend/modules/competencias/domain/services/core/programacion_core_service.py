"""La PROGRAMACIÓN de los encuentros: intervalo y solapamiento.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

`RN-K03`: "Nunca solapar un equipo en dos encuentros al mismo horario cuando
la disciplina/regla lo prohíba".

**La regla que este módulo aplica es la GLOBAL de la EDICIÓN**: ninguna
regla de solapamiento por disciplina está congelada en ningún contrato, así
que aquí no se inventa una. Un equipo no puede jugar DOS encuentros a la vez,
aunque sea en competencias distintas de la misma edición: es el mismo equipo
físico.

**Los intervalos son SEMI-ABERTOS** (`[inicio, fin)`): dos encuentros que sólo
se tocan (el fin de uno es el inicio del otro) NO se solapan.

**Un encuentro CANCELADO no reserva la franja** del equipo.

**Sin `select_for_update`:** SQLite no lo soporta y el proyecto ya lo tiene
documentado (`F-55`). El control de concurrencia de este módulo es el
BLOQUEO OPTIMISTA por versión (`expected_version`), que es la protección que
el propio contrato pide (`frontend/05` §6).
"""

from django.db.models import Q

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import HorarioInvalidoError
from modules.competencias.domain.models import Encuentro


class ProgramacionCoreService:
    """Intervalo válido y detección de solapamiento del horario."""

    @staticmethod
    def validar_horario(competencia, inicio, fin) -> None:
        """El horario es un intervalo POSITIVO del día de la competencia.

        El inicio y el fin comparten la fecha de la competencia: una
        competencia ocurre en un único día.
        """
        if inicio is None or fin is None:
            raise HorarioInvalidoError()
        if fin <= inicio:
            raise HorarioInvalidoError()
        if inicio.date() != competencia.fecha or fin.date() != competencia.fecha:
            raise HorarioInvalidoError()

    @staticmethod
    def equipos_de_encuentro(encuentro) -> list[str]:
        """Los identificadores de los equipos que juegan en el encuentro.

        El solapamiento se mide por EQUIPO, no por participación: el mismo
        equipo no puede estar en dos encuentros a la vez.
        """
        equipos: list[str] = []
        for participante in (encuentro.participante_1, encuentro.participante_2):
            if participante is not None:
                equipos.append(str(participante.equipo_id))
        return equipos

    @staticmethod
    def detectar_solape(
        equipo_ids,
        inicio,
        fin,
        *,
        excluir_encuentro_id=None,
    ) -> list[Encuentro]:
        """Los encuentros de esos equipos que se solapan con el intervalo.

        El `JOIN` con los participantes se resuelve ANTES de mezclarlo con los
        filtros del encuentro: mezclados, el `JOIN` sería multi-valorado y la
        base de datos rechazaría la combinación.
        """
        if not equipo_ids or inicio is None or fin is None:
            return []
        encuentros_de_los_equipos = Encuentro.objects.filter(
            Q(participante_1__equipo_id__in=equipo_ids)
            | Q(participante_2__equipo_id__in=equipo_ids)
        ).values("id")
        consultas = Encuentro.objects.filter(
            id__in=encuentros_de_los_equipos,
            inicio_programado__isnull=False,
            fin_programado__isnull=False,
            inicio_programado__lt=fin,
            fin_programado__gt=inicio,
        ).exclude(estado=EstadoEncuentro.CANCELADO)
        if excluir_encuentro_id is not None:
            consultas = consultas.exclude(id=excluir_encuentro_id)
        return list(consultas)


__all__ = ["ProgramacionCoreService"]
