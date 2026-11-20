"""Servicios core de `Encuentro`: participantes, bye, enlace y estado.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

Son SYNC y NO abren transacción. El ciclo de vida del encuentro es:

    BORRADOR → PROGRAMADO → EN_CURSO → FINALIZADO
        └──────────────┴──────────────→ CANCELADO

Un BYE manual es la ÚNICA vía de `BORRADOR` a `FINALIZADO`: el bye lo decide
el administrador y NUNCA lo inventa el sistema (`frontend/05` §6).

**El ganador es AUTORITATIVO**: ocupa uno de los dos slots (restricción
`competencia_encuentro_ganador_en_slot`). Ningún comando permite registrar un
ganador que no esté en un slot.

**El enlace y su slot viajan juntos** (restricción
`competencia_encuentro_enlace_slot`): uno sin el otro no significa nada.

**Los enlaces avanzan a rondas POSTERIORES** (`frontend/05` §6): un enlace a
una ronda anterior o a la misma crearía un CICLO, así que se rechaza.
"""

from django.utils import timezone

from modules.competencias.domain.constants import (
    MAXIMO_ORDEN,
    MINIMO_ORDEN,
    EstadoEncuentro,
    EstadoRonda,
    SlotDestino,
)
from modules.competencias.domain.exceptions import (
    ByeInvalidoError,
    EnlaceInvalidoError,
    HorarioInvalidoError,
    OrdenDuplicadoError,
    ParticipanteInvalidoError,
    TransicionInvalidaError,
)
from modules.competencias.domain.models import CompetenciaEquipo, Encuentro, Ronda
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroCreateData,
)
from modules.competencias.domain.services.core.base_service import BaseCoreService

#: Transiciones legales del encuentro.
TRANSICIONES_ENCUENTRO: dict[str, set[str]] = {
    EstadoEncuentro.BORRADOR: {EstadoEncuentro.PROGRAMADO, EstadoEncuentro.CANCELADO},
    EstadoEncuentro.PROGRAMADO: {
        EstadoEncuentro.BORRADOR,
        EstadoEncuentro.EN_CURSO,
        EstadoEncuentro.CANCELADO,
    },
    EstadoEncuentro.EN_CURSO: {EstadoEncuentro.FINALIZADO, EstadoEncuentro.CANCELADO},
    EstadoEncuentro.FINALIZADO: set(),
    EstadoEncuentro.CANCELADO: set(),
}

#: Estados tras los que el encuentro ya no admite cambios.
ESTADOS_TERMINALES_ENCUENTRO = {
    EstadoEncuentro.FINALIZADO,
    EstadoEncuentro.CANCELADO,
}


class EncuentroCoreService(BaseCoreService):
    """Operaciones sync sobre `Encuentro` — el llamador posee la transacción."""

    def crear(self, ronda: Ronda, data: EncuentroCreateData) -> Encuentro:
        """Crea el encuentro, posiblemente VACÍO.

        Un encuentro sin participantes y sin horario es un `BORRADOR`
        LEGÍTIMO: el cuadro puede estar vacío o parcial (`frontend/05` §1.3).
        """
        if ronda.estado != EstadoRonda.ACTIVA:
            raise TransicionInvalidaError()
        if data.orden < MINIMO_ORDEN or data.orden > MAXIMO_ORDEN:
            raise OrdenDuplicadoError()
        if Encuentro.objects.filter(ronda=ronda, orden=data.orden).exists():
            raise OrdenDuplicadoError()
        encuentro = Encuentro(
            ronda=ronda,
            orden=data.orden,
            estado=EstadoEncuentro.BORRADOR,
        )
        return self.persistir_nuevo(encuentro)

    def asignar_participantes(
        self,
        encuentro: Encuentro,
        *,
        participante_1_id,
        participante_2_id,
        expected_version: int | None,
        motivo: str | None,
    ) -> Encuentro:
        """Mueve los equipos de los slots.

        Mover un slot es una operación SENSIBLE: exige motivo auditado. Los
        participantes tienen que pertenecer a la MISMA competencia: un equipo
        de otro torneo no entra aquí.
        """
        self.exigir_no_terminal(encuentro, ESTADOS_TERMINALES_ENCUENTRO)
        ya_aplicado = (
            self._mismo_participante(encuentro.participante_1_id, participante_1_id)
            and self._mismo_participante(encuentro.participante_2_id, participante_2_id)
        )
        self.aplicar_cas(encuentro, expected_version, ya_aplicado)
        if ya_aplicado:
            return encuentro

        self.exigir_motivo(motivo)
        participante_1, participante_2 = self._validar_participantes(
            encuentro,
            participante_1_id,
            participante_2_id,
        )
        encuentro.participante_1 = participante_1
        encuentro.participante_2 = participante_2
        return self.persistir_cambio(encuentro)

    def configurar_bye(
        self,
        encuentro: Encuentro,
        *,
        expected_version: int | None,
        motivo: str | None,
    ) -> Encuentro:
        """Configura un BYE MANUAL.

        Un bye tiene EXACTAMENTE un equipo, sin horario, sin marcador, y es
        FINAL: ese equipo es el ganador. El bye NUNCA lo elige el sistema.
        """
        if encuentro.es_bye and encuentro.estado == EstadoEncuentro.FINALIZADO:
            # Idempotencia: el encuentro YA es un bye manual resuelto.
            return encuentro
        if (
            encuentro.inicio_programado is not None
            or encuentro.fin_programado is not None
        ):
            raise HorarioInvalidoError()
        if (encuentro.participante_1 is None) == (encuentro.participante_2 is None):
            raise ByeInvalidoError()
        if encuentro.estado != EstadoEncuentro.BORRADOR:
            raise TransicionInvalidaError()

        self.aplicar_cas(encuentro, expected_version)
        self.exigir_motivo(motivo)

        participante = encuentro.participante_1 or encuentro.participante_2
        encuentro.es_bye = True
        encuentro.ganador = participante
        encuentro.estado = EstadoEncuentro.FINALIZADO
        encuentro.finalizado_en = timezone.now()
        return self.persistir_cambio(encuentro)

    def enlazar(
        self,
        encuentro: Encuentro,
        *,
        siguiente_encuentro_id,
        slot_destino,
        expected_version: int | None,
        motivo: str | None,
    ) -> Encuentro:
        """Enlaza el encuentro con el destino que recibe a su ganador.

        El enlace y su slot viajan juntos y el destino tiene que estar en una
        ronda POSTERIOR: un enlace hacia atrás crearía un ciclo
        (`frontend/05` §6).
        """
        self.exigir_no_terminal(encuentro, ESTADOS_TERMINALES_ENCUENTRO)
        ya_aplicado = (
            str(encuentro.siguiente_encuentro_id or "") == str(siguiente_encuentro_id or "")
            and (encuentro.slot_destino or "") == (slot_destino or "")
        )
        self.aplicar_cas(encuentro, expected_version, ya_aplicado)
        if ya_aplicado:
            return encuentro

        self.exigir_motivo(motivo)
        destino = self._validar_destino(encuentro, siguiente_encuentro_id, slot_destino)
        encuentro.siguiente_encuentro = destino
        encuentro.slot_destino = slot_destino
        return self.persistir_cambio(encuentro)

    def cambiar_estado(
        self,
        encuentro: Encuentro,
        nuevo_estado: str,
        *,
        expected_version: int | None,
        motivo: str | None,
    ) -> Encuentro:
        """Mueve el encuentro por su ciclo de vida.

        El resultado de un encuentro normal NO se registra por aquí: lo
        registra el flujo de resultado. Por esta vía sólo se llega a
        `FINALIZADO` desde un BYE, que ya tiene su ganador.
        """
        if encuentro.estado == nuevo_estado:
            return encuentro
        permitidos = TRANSICIONES_ENCUENTRO.get(encuentro.estado, set())
        if nuevo_estado not in permitidos:
            raise TransicionInvalidaError()
        if nuevo_estado == EstadoEncuentro.FINALIZADO and encuentro.ganador_id is None:
            raise TransicionInvalidaError()

        self.aplicar_cas(encuentro, expected_version)
        self.exigir_motivo(motivo)

        if nuevo_estado == EstadoEncuentro.EN_CURSO and not encuentro.iniciado_en:
            encuentro.iniciado_en = timezone.now()
        if nuevo_estado == EstadoEncuentro.BORRADOR:
            # Volver al borrador retira la programación publicada.
            encuentro.inicio_programado = None
            encuentro.fin_programado = None
        if nuevo_estado == EstadoEncuentro.CANCELADO:
            # Un encuentro cancelado libera la franja del equipo: no la
            # reserva. La detección de solapamiento lo excluye.
            encuentro.iniciado_en = None

        encuentro.estado = nuevo_estado
        return self.persistir_cambio(encuentro)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _mismo_participante(actual, solicitado) -> bool:
        """Si el slot ya contiene exactamente la participación pedida."""
        return str(actual or "") == str(solicitado or "")

    @staticmethod
    def _validar_participantes(encuentro, participante_1_id, participante_2_id):
        """Los participantes existen, son de la competencia y son distintos."""
        ids = [i for i in (participante_1_id, participante_2_id) if i]
        if not ids:
            return None, None
        participaciones = {
            str(p.id): p
            for p in CompetenciaEquipo.objects.filter(id__in=ids).select_related(
                "competencia"
            )
        }
        if len(participaciones) != len(set(str(i) for i in ids)):
            raise ParticipanteInvalidoError()

        competencia_id = str(encuentro.ronda.competencia_id)
        for identificador in ids:
            participacion = participaciones.get(str(identificador))
            if participacion is None:
                raise ParticipanteInvalidoError()
            if str(participacion.competencia_id) != competencia_id:
                raise ParticipanteInvalidoError()

        if (
            participante_1_id
            and participante_2_id
            and str(participante_1_id) == str(participante_2_id)
        ):
            raise ParticipanteInvalidoError()

        return (
            participaciones.get(str(participante_1_id)) if participante_1_id else None,
            participaciones.get(str(participante_2_id)) if participante_2_id else None,
        )

    @staticmethod
    def _validar_destino(encuentro: Encuentro, siguiente_encuentro_id, slot_destino):
        """El destino existe, es de la competencia, es posterior y el slot vale."""
        if not siguiente_encuentro_id or not slot_destino:
            raise EnlaceInvalidoError()
        if slot_destino not in SlotDestino.values:
            raise EnlaceInvalidoError()
        destino = (
            Encuentro.objects.select_related("ronda")
            .filter(id=siguiente_encuentro_id)
            .first()
        )
        if destino is None:
            raise EnlaceInvalidoError()
        if str(destino.ronda.competencia_id) != str(encuentro.ronda.competencia_id):
            raise EnlaceInvalidoError()
        if destino.ronda.orden <= encuentro.ronda.orden:
            # Un enlace a la misma ronda o a una anterior crearía un CICLO.
            raise EnlaceInvalidoError()
        if str(destino.id) == str(encuentro.id):
            raise EnlaceInvalidoError()
        return destino


__all__ = [
    "ESTADOS_TERMINALES_ENCUENTRO",
    "TRANSICIONES_ENCUENTRO",
    "EncuentroCoreService",
]
