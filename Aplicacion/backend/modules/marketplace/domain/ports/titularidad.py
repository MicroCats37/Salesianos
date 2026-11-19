"""El puerto de TITULARIDAD del actor (`DOM-05`).

Contract: `contract/django-app-architecture-contract.md` §4.10

El comprador de un pedido es la PERSONA de la cuenta autenticada. Este
puerto reproduce la primitiva de `usuarios` (su dueño, `FREEZE-ID-1.0.0`,
`FR-03` §2.1) sin que el dominio de `marketplace` importe ese módulo.

El documento de identidad NO es una credencial (RN-U04): el único origen
admisible del sujeto de una titularidad es la cuenta autenticada.
"""

from abc import ABC, abstractmethod


class ITitularidadActorService(ABC):
    """La persona del actor autenticado."""

    @abstractmethod
    def persona_id_del_actor(self, usuario) -> str | None:
        """El identificador de la persona vinculada al actor, o `None`.

        Args:
            usuario: la cuenta autenticada (`request.auth`).

        Returns:
            El identificador de la `Persona` vinculada, o `None` cuando la
            cuenta no tiene ninguna.
        """
        ...


__all__ = ["ITitularidadActorService"]
