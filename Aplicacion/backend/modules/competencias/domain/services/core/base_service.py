"""Helpers compartidos por los servicios core del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

Los servicios core son SYNC y NO abren `transaction.atomic()`: la atomicidad
la posee el flujo (§4.4). Aquí viven las TRES reglas que comparte todo
comando del cuadro:

1. **El bloqueo optimista** (`expected_version`): compare-and-swap. El
   cliente viaja la versión que conoce y el servidor la compara ANTES de
   escribir; si ya no es la actual, la operación se rechaza con
   `RESOURCE_CHANGED` (409) y NO se escribe nada (`frontend/05` §5).
2. **El motivo auditado** es OBLIGATORIO en toda operación protegida
   (5..500 caracteres): sin él, `MOTIVO_REQUERIDO` (422).
3. **El contador de versión** se incrementa en cada escritura: es el reloj
   que los clientes comparan.
"""

from modules.competencias.domain.constants import (
    MAXIMO_MOTIVO,
    MINIMO_MOTIVO,
)
from modules.competencias.domain.exceptions import (
    GanadorInvalidoError,
    MotivoRequeridoError,
    TransicionInvalidaError,
    VersionDesactualizadaError,
)


class BaseCoreService:
    """Helpers compartidos por los servicios core del módulo."""

    @staticmethod
    def validar_version(actual: int, expected_version: int | None) -> None:
        """Compare-and-swap: rechaza el comando cuando la versión es obsoleta.

        `expected_version` es OPCIONAL: cuando el llamador no la aporta, el
        comando se ejecuta SIN bloqueo optimista (uso interno). La capa HTTP
        la aporta SIEMPRE.
        """
        if expected_version is None:
            return
        if int(actual) != int(expected_version):
            raise VersionDesactualizadaError()

    @staticmethod
    def aplicar_cas(
        entidad,
        expected_version: int | None,
        ya_aplicado: bool = False,
    ) -> None:
        """Idempotencia primero, bloqueo optimista después.

        Cuando el estado persistido YA es la intención pedida, el comando es
        un NO-OP: no escribe nada. Si no, la versión con la que trabajó el
        llamador tiene que ser la actual: si no, el cambio se rechaza SIN
        efecto parcial.
        """
        if ya_aplicado:
            return
        BaseCoreService.validar_version(entidad.version, expected_version)

    @staticmethod
    def exigir_motivo(motivo: str | None) -> str:
        """El motivo auditado de la operación, o el error de motivorequired.

        Mover slots o byes, cambiar horarios, ganadores, enlaces o la
        propagación EXIGE siempre un motivo auditado.
        """
        if not motivo:
            raise MotivoRequeridoError()
        limpio = motivo.strip()
        if len(limpio) < MINIMO_MOTIVO or len(limpio) > MAXIMO_MOTIVO:
            raise MotivoRequeridoError()
        return limpio

    @staticmethod
    def exigir_no_terminal(entidad, estados_terminales) -> None:
        """Rechaza el comando cuando la entidad ya alcanzó un estado final."""
        if entidad.estado in estados_terminales:
            raise TransicionInvalidaError()

    @staticmethod
    def participante_del_slot(encuentro, participante_id):
        """El participante que ocupa uno de los dos slots.

        El ganador es AUTORITATIVO y TIENE que ocupar uno de los slots
        (restricción `competencia_encuentro_ganador_en_slot`).
        """
        for participante in (
            encuentro.participante_1,
            encuentro.participante_2,
        ):
            if (
                participante is not None
                and str(participante.id) == str(participante_id)
            ):
                return participante
        raise GanadorInvalidoError()

    @staticmethod
    def persistir_nuevo(entidad, motivo: str | None = None):
        """Persiste una entidad NUEVA (versión 1)."""
        entidad.version = 1
        entidad.save()
        return entidad

    @staticmethod
    def persistir_cambio(entidad, motivo: str | None = None):
        """Persiste un cambio incrementando el contador de versión."""
        entidad.version = (entidad.version or 0) + 1
        entidad.save()
        return entidad


__all__ = ["BaseCoreService"]
