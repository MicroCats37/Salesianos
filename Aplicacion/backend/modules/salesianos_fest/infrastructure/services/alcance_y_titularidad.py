"""Adaptadores de los puertos que cruzan a los módulos DUEÑOS.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Cada adaptador traduce una primitiva de un módulo ajeno al puerto que declara
este módulo. El adaptador NO decide: sólo traduce.

- `AlcanceEdicionAdapter` — el alcance de edición (`modules.eventos`).
- `TitularidadAdapter` — la titularidad (`modules.usuarios`).
- `ResolucionPersonaAdapter` — la resolución de una identidad por documento
  (`modules.usuarios`), que `FL-05` paso 2 permite usar para agregar al pool
  una persona que todavía no está en la inscripción.
"""

from modules.salesianos_fest.domain.ports import (
    IAlcanceEdicionService,
    IResolucionPersonaService,
    ITitularidadService,
)


class AlcanceEdicionAdapter(IAlcanceEdicionService):
    """Puente con el servicio de alcance de `modules.eventos`.

    Reproduce el ORDEN ÚNICO congelado de `FR-02` §2.2 sin duplicarlo: el
    módulo `eventos` es su dueño y este adaptador no decide nada.
    """

    def __init__(self, scope_service=None):
        from modules.eventos.domain.services.core.edicion_scope_service import (
            EdicionScopeService,
        )

        self.scope_service = scope_service or EdicionScopeService()

    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """Nivel 1 del orden congelado. NUNCA hay fallback."""
        return self.scope_service.resolver_explicita(
            edicion_id,
            exigir_publicada=exigir_publicada,
        )

    def resolver_actual(
        self,
        *,
        ediciones_activas_actor=None,
        exigir_publicada: bool = False,
        permitir_publicada_por_defecto: bool = True,
    ):
        """Niveles 2, 3 y 4 del orden congelado."""
        return self.scope_service.resolver_actual(
            ediciones_activas_actor=ediciones_activas_actor,
            exigir_publicada=exigir_publicada,
            permitir_publicada_por_defecto=permitir_publicada_por_defecto,
        )


class TitularidadAdapter(ITitularidadService):
    """Puente con las primitivas de titularidad de `modules.usuarios`.

    `FR-03` §2.1 regla 1: la comprobación de titularidad es una función del
    MÓDULO DUEÑO del recurso. Este adaptador NO decide: sólo traduce las
    primitivas puras al puerto del módulo.
    """

    def __init__(self, titularidad_service=None):
        from modules.usuarios.domain.services.core.titularidad_service import (
            TitularidadService,
        )

        self.titularidad_service = titularidad_service or TitularidadService()

    def persona_id_del_actor(self, usuario) -> str | None:
        """El identificador de la persona del actor, o `None`."""
        persona = self.titularidad_service.persona_del_actor(usuario)
        if persona is None:
            return None
        return str(persona.id)

    def es_responsable(self, persona_id: str | None, responsable_id: str) -> bool:
        """Si la persona es la responsable del recurso indicado."""
        if not persona_id or not responsable_id:
            return False
        return str(persona_id) == str(responsable_id)


class ResolucionPersonaAdapter(IResolucionPersonaService):
    """Puente con el padrón de identidades de `modules.usuarios`.

    `usuarios` es el dueño del padrón (`FREEZE-ID-1.0.0`, `FR-03` §3). Este
    adaptador hace una CONSULTA LOCAL por documento: si la identidad no
    existe, no se crea ni se consulta ninguna fuente externa. Crear o
    confirmar una identidad es de `usuarios`, no de este módulo.
    """

    def __init__(self, persona_selector=None):
        from modules.usuarios.domain.selectors import PersonaSelector

        self.persona_selector = persona_selector or PersonaSelector()

    def resolver_por_documento(self, tipo_documento: str, numero_documento: str):
        """La persona con ese documento en el padrón local, o `None`."""
        if not tipo_documento or not numero_documento:
            return None
        return self.persona_selector.obtener_por_documento(
            tipo_documento,
            numero_documento,
        )

    def resolver_por_id(self, persona_id):
        """La persona con ese identificador, o `None`."""
        if not persona_id:
            return None
        return self.persona_selector.obtener_por_id(str(persona_id))


__all__ = [
    "AlcanceEdicionAdapter",
    "ResolucionPersonaAdapter",
    "TitularidadAdapter",
]
