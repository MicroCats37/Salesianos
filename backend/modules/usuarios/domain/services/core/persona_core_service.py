"""
PersonaCoreService — operaciones ORM síncronas para Persona.

NO usa transaction.atomic() internamente — el llamador (flujo) provee la transacción si es necesaria.
"""
from modules.usuarios.domain.models import Persona


class PersonaCoreService:
    """
    Operaciones síncronas para Persona: búsqueda y creación.
    NO usa transaction.atomic() — el llamador lo provee si es necesario.
    """

    def _get_persona_por_documento(
        self, tipo_documento: str, numero_documento: str
    ) -> Persona | None:
        """Sync: obtiene Persona por tipo y número de documento."""
        try:
            return Persona.objects.get(
                tipo_documento=tipo_documento,
                numero_documento=numero_documento
            )
        except Persona.DoesNotExist:
            return None

    def _get_persona_por_id(self, persona_id: str) -> Persona | None:
        """Sync: obtiene Persona por UUID ID."""
        try:
            return Persona.objects.get(id=persona_id)
        except Persona.DoesNotExist:
            return None

    def _crear_persona(self, data: dict) -> Persona:
        """Sync: crea una nueva Persona con los datos proporcionados."""
        return Persona.objects.create(**data)