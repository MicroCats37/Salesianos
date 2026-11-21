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

from modules.usuarios.domain.constants import GeneroChoices
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.schemas import (
    PersonaCreateData,
    normalizar_numero_documento,
)

logger = logging.getLogger(__name__)

#: Los géneros canónicos del padrón. Un género fuera de este vocabulario
#: NO se corrige: se guarda como estaba.
GENEROS_CANONICOS = frozenset(
    {GeneroChoices.MASCULINO.value, GeneroChoices.FEMENINO.value}
)


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

    def corregir_genero(self, persona: Persona, genero: str) -> tuple[str, str]:
        """Corrige SÓLO el género de una identidad que YA existe.

        Es la ÚNICA corrección que el padrón admite sobre una `Persona`
        viva: los NOMBRES y los APELLIDOS nunca se reescriben (`FR-03`
        §1.1 — la identidad que ya existe no se reescribe; el género es la
        ÚNICA excepción, y sólo cuando alguien lo declara EXPLÍCITAMENTE).

        La escritura es MÍNIMA: se toca el campo `genero` y nada más.

        Args:
            persona: la identidad a corregir.
            genero: el género canónico declarado (`M` o `F`).

        Returns:
            La tupla `(genero_anterior, genero_nuevo)`. Si el género declarado
            está vacío, no es canónico o ya es el almacenado, la tupla
            devuelve el género almacenado en ambos posiciones: NO hay
            corrección.
        """
        anterior = (persona.genero or "").strip().upper()
        nuevo = (genero or "").strip().upper()

        if nuevo not in GENEROS_CANONICOS or nuevo == anterior:
            return anterior, anterior

        persona.genero = nuevo
        persona.save(update_fields=["genero"])

        return anterior, nuevo


__all__ = ["GENEROS_CANONICOS", "PersonaCoreService"]
