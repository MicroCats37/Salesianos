"""Adaptador de la CORRECCIÓN del género de una identidad del padrón.

Change: `admin-client-purchases-and-participants`

Traduce la intención del dominio a las primitivas del módulo DUEÑO del padrón
(`modules.usuarios`). El adaptador NO decide: sólo traduce.

- **Corrige SÓLO el género**: los nombres y los apellidos de una `Persona`
  que ya existe NUNCA se reescriben (`FR-03` §1.1).
- **No inventa el género**: sin género canónico declarado, NO se toca nada.
- **No crea una cuenta**: la identidad civil sigue sin `Usuario`.
- **No abre su propia transacción**: la corrección comparte la transacción
  del flujo que la pide (`contract/django-app-architecture-contract.md`
  §4.3 — el core no abre `transaction.atomic()`).
"""

from modules.salesianos_fest.domain.ports import ICorreccionGeneroPersonaService


class CorreccionGeneroPersonaAdapter(ICorreccionGeneroPersonaService):
    """Puente con el padrón de identidades de `modules.usuarios`.

    `usuarios` es el dueño del padrón (`FREEZE-ID-1.0.0`, `FR-03` §3): este
    adaptador pide al DUEÑO la corrección mínima y devuelve lo que cambió.
    """

    def __init__(self, persona_core=None):
        from modules.usuarios.domain.services.core.persona_core_service import (
            PersonaCoreService,
        )

        self.persona_core = persona_core or PersonaCoreService()

    def corregir_genero(self, persona, genero: str) -> tuple[str, str]:
        """Corrige el género de la identidad, si se declara otro.

        Args:
            persona: la identidad ya existente que hay que corregir.
            genero: el género canónico declarado (`M` o `F`).

        Returns:
            La tupla `(genero_anterior, genero_nuevo)`.
        """
        return self.persona_core.corregir_genero(persona, genero)


__all__ = ["CorreccionGeneroPersonaAdapter"]
