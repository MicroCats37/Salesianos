"""
Shared helpers of the core services of the module.

The core services are SYNC and never open a transaction: the flow owns the
atomicity (contract/django-app-architecture-contract.md §4.3). These helpers
implement the three rules shared by every command of the bracket:

- the optimistic lock (`expected_version`) — compare-and-swap,
- the mandatory motive of the protected mutations (design: motivo 5..500),
- the version counter and the audit trail of every save.
"""
from ...exceptions import (
    InvalidStateTransitionError,
    InvalidWinnerError,
    ReasonRequiredError,
    ResourceChangedError,
)

MINIMO_MOTIVO = 5
MAXIMO_MOTIVO = 500


class BaseCoreService:
    """Helpers shared by the sync core services of the module."""

    @staticmethod
    def validar_version(actual: int, expected_version: int | None) -> None:
        """Compare-and-swap: reject the command when the version is stale.

        `expected_version` is optional: when the caller does not provide it
        the command runs without optimistic locking (the HTTP layer of Phase 3
        always provides it).
        """
        if expected_version is None:
            return
        if int(actual) != int(expected_version):
            raise ResourceChangedError()

    @staticmethod
    def aplicar_cas(
        entidad,
        expected_version: int | None,
        ya_aplicado: bool = False,
    ) -> None:
        """Idempotency first, then the optimistic lock.

        When the persisted state already matches the requested intent the
        command is a no-op: it returns without writing anything. Otherwise
        the version the caller worked on must be the current one, otherwise
        the edit is rejected without any partial effect.
        """
        if ya_aplicado:
            return
        BaseCoreService.validar_version(entidad.version, expected_version)

    @staticmethod
    def exigir_motivo(motivo: str | None) -> str:
        """Return the motive of the change or reject the command.

        Moving slots or byes, changing schedules, winners, links or the
        propagation ALWAYS requires an audited motive (design: 5..500).
        """
        if not motivo:
            raise ReasonRequiredError()
        limpio = motivo.strip()
        if len(limpio) < MINIMO_MOTIVO or len(limpio) > MAXIMO_MOTIVO:
            raise ReasonRequiredError()
        return limpio

    @staticmethod
    def exigir_no_terminal(entidad, estados_terminales) -> None:
        """Reject the command when the entity already reached a final state."""
        if entidad.estado in estados_terminales:
            raise InvalidStateTransitionError()

    @staticmethod
    def participante_del_slot(encuentro, participante_id):
        """Return the participant that occupies one of the two slots.

        The winner is authoritative and it MUST occupy one of the slots
        (model constraint `ck_encuentro_ganador_en_slot`).
        """
        for participante in (
            encuentro.participante_1,
            encuentro.participante_2,
        ):
            if participante is not None and str(participante.id) == str(participante_id):
                return participante
        raise InvalidWinnerError()

    @staticmethod
    def persistir_nuevo(entidad, actor=None, motivo: str | None = None):
        """Persist a NEW entity (version 1) attaching the audit data."""
        entidad.save(history_user=actor, history_change_reason=motivo)
        return entidad

    @staticmethod
    def persistir_cambio(entidad, actor=None, motivo: str | None = None):
        """Update an entity bumping its optimistic-locking counter."""
        entidad.version = (entidad.version or 0) + 1
        entidad.save(history_user=actor, history_change_reason=motivo)
        return entidad
