"""El RESULTADO autoritativo de un encuentro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

**El ganador es AUTORITATIVO**: lo declara el administrador y NUNCA se
deduce del marcador. Los puntajes son INFORMATIVOS: se guardan tal como se
dan y no infieren ni contradicen al ganador (`frontend/05` §6: "No calcular
automáticamente ganadores desde el marcador en React").

**Sólo un encuentro EN CURSO acepta un resultado** (`EstadoEncuentro`): un
encuentro `BORRADOR` no se ha jugado y uno `FINALIZADO` ya tiene su
resultado. Un BYE es final por definición y nunca llega aquí: su ganador lo
establece el bye.

El orden del comando es fijo:

1. se compara primero la intención COMPLETA: si ya está aplicada, el comando
   no escribe NADA (reintento idempotente);
2. si no, la versión con la que trabajó el cliente tiene que ser la actual;
3. el estado tiene que admitir un resultado y el ganador tiene que ocupar un
   slot;
4. el cambio se escribe con su motivo auditado.
"""

from django.utils import timezone

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import TransicionInvalidaError
from modules.competencias.domain.models import Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    ResultadoEncuentroData,
)
from modules.competencias.domain.services.core.base_service import BaseCoreService


class ResultadoCoreService(BaseCoreService):
    """Comandos sync sobre el resultado autoritativo de un encuentro."""

    def registrar(
        self,
        encuentro: Encuentro,
        data: ResultadoEncuentroData,
        *,
        expected_version: int | None,
        motivo: str | None,
    ) -> Encuentro:
        """Registra el ganador del encuentro y lo finaliza."""
        # 1. Idempotencia: la intención COMPLETA se compara ANTES de la
        #    versión, así que un reintento exacto no escribe nada.
        if self._mismo_resultado(encuentro, data):
            return encuentro

        # 2. Sólo un encuentro EN CURSO acepta un resultado. Un bye es final
        #    por definición y nunca llega a este comando.
        if encuentro.estado != EstadoEncuentro.EN_CURSO:
            raise TransicionInvalidaError()

        # 3. El ganador tiene que ocupar uno de los dos slots.
        ganador = self.participante_del_slot(encuentro, data.ganador_id)

        # 4. Bloqueo optimista y motivo auditado.
        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)

        # 5. Escritura. Los puntajes se guardan tal como se dieron: son
        #    informativos y NUNCA reemplazan al ganador autoritativo.
        encuentro.ganador = ganador
        encuentro.puntaje_1 = data.puntaje_1
        encuentro.puntaje_2 = data.puntaje_2
        encuentro.marcador_detalle = data.marcador_detalle or ""
        encuentro.estado = EstadoEncuentro.FINALIZADO
        encuentro.finalizado_en = timezone.now()
        return self.persistir_cambio(encuentro, motivo)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _mismo_resultado(
        encuentro: Encuentro,
        data: ResultadoEncuentroData,
    ) -> bool:
        """Si el estado persistido YA es el resultado pedido."""
        return (
            encuentro.estado == EstadoEncuentro.FINALIZADO
            and str(encuentro.ganador_id or "") == str(data.ganador_id)
            and encuentro.puntaje_1 == data.puntaje_1
            and encuentro.puntaje_2 == data.puntaje_2
            and (encuentro.marcador_detalle or "") == (data.marcador_detalle or "")
        )


__all__ = ["ResultadoCoreService"]
