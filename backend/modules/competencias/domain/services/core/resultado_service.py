"""
Core sync service of the RESULT of an encounter.

The winner is AUTHORITATIVE (spec: "Solo un participante MUST poder ser
ganador" and "el ganador, que es autoritativo"). The scores are optional and
purely informative: they are stored as they are given and they NEVER
determine nor contradict the winner (design: "los puntajes son opcionales e
informativos; no infieren ni validan al ganador autoritativo").

The command follows the order of the design:

1. the COMPLETE intention is compared first: when it is already applied the
   command writes nothing at all (idempotent replay),
2. otherwise the version the caller worked on must be the current one,
3. the state must accept a result and the winner must occupy a slot,
4. the change is written with the audited motive.
"""
from django.utils import timezone

from ...constants import EstadoEncuentroChoices
from ...exceptions import InvalidStateTransitionError
from ...models import Encuentro
from ...schemas.competencias_schemas import ResultadoEncuentroData
from .base_service import BaseCoreService


class ResultadoCoreService(BaseCoreService):
    """Sync commands over the authoritative result of an encounter."""

    def registrar_resultado(
        self,
        encuentro: Encuentro,
        data: ResultadoEncuentroData,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Register the winner of the encounter and finalize it."""
        # 1. Idempotency: the complete intention is compared BEFORE the
        #    version, so an exact replay never writes anything.
        if self._mismo_resultado(encuentro, data):
            return encuentro

        # 2. Only a running encounter accepts a result. A bye is final by
        #    definition and never reaches this command.
        if encuentro.estado != EstadoEncuentroChoices.EN_CURSO:
            raise InvalidStateTransitionError()

        # 3. The winner must occupy one of the two slots.
        ganador = self.participante_del_slot(encuentro, data.ganador_id)

        # 4. Optimistic lock and audited motive.
        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)

        # 5. Write. The scores are stored as they were given: they are
        #    informative and they never override the authoritative winner.
        encuentro.ganador = ganador
        encuentro.puntaje_1 = data.puntaje_1
        encuentro.puntaje_2 = data.puntaje_2
        encuentro.marcador_detalle = data.marcador_detalle or ""
        encuentro.estado = EstadoEncuentroChoices.FINALIZADO
        encuentro.finalizado_en = timezone.now()
        return self.persistir_cambio(encuentro, actor, motivo)

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _mismo_resultado(
        encuentro: Encuentro,
        data: ResultadoEncuentroData,
    ) -> bool:
        """True when the persisted state already IS the requested result."""
        return (
            encuentro.estado == EstadoEncuentroChoices.FINALIZADO
            and str(encuentro.ganador_id or "") == str(data.ganador_id)
            and encuentro.puntaje_1 == data.puntaje_1
            and encuentro.puntaje_2 == data.puntaje_2
            and (encuentro.marcador_detalle or "") == (data.marcador_detalle or "")
        )
