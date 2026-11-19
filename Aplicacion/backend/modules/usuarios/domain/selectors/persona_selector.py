"""
Selectores de lectura del módulo `usuarios`.

`contract/django-app-architecture-contract.md` §8: un selector existe cuando
la query se reutiliza, es compleja o debe ser mockeable. Estos son sync y
NO contienen lógica de negocio.
"""

from typing import Optional

from modules.usuarios.domain.models import Persona, Usuario
from modules.usuarios.domain.schemas import (
    normalizar_numero_documento,
    normalizar_tipo_documento,
)


class PersonaSelector:
    """Consultas de lectura sobre `Persona`."""

    def obtener_por_documento(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> Optional[Persona]:
        """Devuelve la persona con ese documento exacto, o `None`.

        La coincidencia es EXACTA sobre `(tipo_documento, numero_documento)`
        normalizados: no hay búsqueda difusa ni listado.
        """
        return (
            Persona.objects.filter(
                tipo_documento=normalizar_tipo_documento(tipo_documento),
                numero_documento=normalizar_numero_documento(numero_documento),
            )
            .first()
        )

    def obtener_por_id(self, persona_id: str) -> Optional[Persona]:
        """Devuelve la persona con ese id, o `None`."""
        return Persona.objects.filter(id=persona_id).first()


class UsuarioSelector:
    """Consultas de lectura sobre `Usuario`."""

    def obtener_por_persona(self, persona_id: str) -> Optional[Usuario]:
        """Devuelve la cuenta vinculada a esa persona, o `None`."""
        return Usuario.objects.filter(persona_fk_id=persona_id).first()

    def obtener_por_id(self, usuario_id: str) -> Optional[Usuario]:
        """Devuelve la cuenta con ese id, o `None`."""
        return Usuario.objects.filter(id=usuario_id).first()


__all__ = ["PersonaSelector", "UsuarioSelector"]
