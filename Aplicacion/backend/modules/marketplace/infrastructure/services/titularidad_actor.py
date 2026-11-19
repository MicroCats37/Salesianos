"""`TitularidadActorAdapter` — la persona del actor autenticado.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.10

Puente con las primitivas de titularidad de `modules.usuarios`, que es su
dueño (`FREEZE-ID-1.0.0`, `FR-03` §2.1). Este adaptador NO decide: sólo
reproduce la primitiva pura en el puerto del módulo.

El import es perezoso a propósito: el grafo de módulos queda acíclico y el
orden de carga de Django no importa.
"""

from modules.marketplace.domain.ports.titularidad import ITitularidadActorService


class TitularidadActorAdapter(ITitularidadActorService):
    """La persona vinculada a la cuenta autenticada."""

    def __init__(self, titularidad_service=None):
        if titularidad_service is None:
            from modules.usuarios.domain.services.core.titularidad_service import (
                TitularidadService,
            )

            titularidad_service = TitularidadService()
        self.titularidad_service = titularidad_service

    def persona_id_del_actor(self, usuario) -> str | None:
        """El identificador de la persona del actor, o `None`.

        El documento de identidad NO es una credencial (RN-U04): el único
        origen admisible del sujeto de una titularidad es la cuenta
        autenticada.
        """
        persona = self.titularidad_service.persona_del_actor(usuario)
        if persona is None:
            return None
        return str(persona.id)


__all__ = ["TitularidadActorAdapter"]
