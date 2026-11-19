"""
`PersonaCoreService` — escritura de identidades civiles.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.1 y §3.2 regla 3.

Es sync y NO abre `transaction.atomic()` propia: la transacción y el
reintento controlado ante `IntegrityError` viven en el flujo
(`contract/django-app-architecture-contract.md` §4.3,
`contract/PLAN_REFACTORIZACION.md` §4 — el `@transaction.atomic` es del
flujo).

El core es ORM puro: sin condiciones de negocio, sin ramas de autorización.
"""

import logging

from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.schemas import (
    PersonaCreateData,
    normalizar_numero_documento,
)

logger = logging.getLogger(__name__)


class PersonaCoreService:
    """Operaciones de escritura sobre `Persona`."""

    def crear(self, data: PersonaCreateData) -> Persona:
        """Crea la persona con ese documento.

        La unicidad la garantiza la `UniqueConstraint` de la base de datos.
        Si el documento ya existe, la base de datos lanza `IntegrityError` y
        el flujo decide: reintento controlado (carrera perdida) o conflicto
        de negocio.
        """
        return Persona.objects.create(**data.model_dump())

    def obtener_por_documento(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> Persona | None:
        """Devuelve la persona con ese documento exacto, o `None`."""
        return (
            Persona.objects.filter(
                tipo_documento=tipo_documento,
                numero_documento=normalizar_numero_documento(numero_documento),
            )
            .first()
        )

    @staticmethod
    def normalizar_documento(numero_documento: str) -> str:
        """Documento normalizado (misma regla que el DTO de alta)."""
        return normalizar_numero_documento(numero_documento)


__all__ = ["PersonaCoreService"]
