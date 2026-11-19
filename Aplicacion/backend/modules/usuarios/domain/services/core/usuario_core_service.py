"""
`UsuarioCoreService` — escritura de cuentas.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2.

Invariante central: el NACIMIENTO DE CUENTA es una operación explícita.
Consultar un documento, resolver una identidad o prellenar datos de la fuente
externa NUNCA crean una `Usuario` (`FR-03` §1.2, `contratos/02` §1).
"""

import logging

from django.db import IntegrityError

from modules.usuarios.domain.exceptions import PersonaDuplicadaError
from modules.usuarios.domain.models import Persona, Usuario

logger = logging.getLogger(__name__)


class UsuarioCoreService:
    """Operaciones de escritura sobre `Usuario`."""

    def crear(
        self,
        username: str,
        password: str,
        email: str | None = None,
        persona: Persona | None = None,
    ) -> Usuario:
        """Crea una cuenta, opcionalmente vinculada a una `Persona`.

        La cuenta puede existir SIN `Persona` (cuentas técnicas, superusuario)
        y la `Persona` puede existir SIN cuenta (comprador invitado,
        beneficiario de un pase).
        """
        return Usuario.objects.create_user(
            username=username,
            password=password,
            email=email or None,
            persona_fk=persona,
        )

    def vincular_persona(self, usuario: Usuario, persona: Persona) -> Usuario:
        """Vincula la cuenta con una `Persona` (1:1)."""
        if usuario.persona_fk_id is not None and usuario.persona_fk_id != persona.id:
            raise PersonaDuplicadaError()
        usuario.persona_fk = persona
        try:
            usuario.save(update_fields=["persona_fk", "updated_at"])
        except IntegrityError:
            logger.warning("La persona ya está vinculada a otra cuenta.")
            raise PersonaDuplicadaError()
        return usuario


__all__ = ["UsuarioCoreService"]
