"""
AcreditacionSelector — query interface for AcreditacionEvento.
"""
from modules.salesianos_fest.domain.models import AcreditacionEvento


class AcreditacionSelector:
    """Query interface for AcreditacionEvento."""

    def obtener_por_id(self, acreditacion_id: str) -> AcreditacionEvento | None:
        """Get an AcreditacionEvento by its ID with select_related."""
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(id=acreditacion_id)
            .first()
        )

    def obtener_por_evento_persona(
        self,
        evento_id: str,
        persona_id: str,
    ) -> AcreditacionEvento | None:
        """Get AcreditacionEvento by evento and persona."""
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(evento_id=evento_id, persona_id=persona_id)
            .first()
        )

    def obtener_por_qr(self, qr_token: str) -> AcreditacionEvento | None:
        """Get AcreditacionEvento by QR code."""
        import uuid
        try:
            uuid_val = uuid.UUID(qr_token)
        except (ValueError, AttributeError):
            return None
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(codigo_qr=uuid_val)
            .first()
        )

    def listar_por_evento(self, evento_id: str) -> list[AcreditacionEvento]:
        """List all acreditaciones for an event."""
        return list(
            AcreditacionEvento.objects
            .select_related("persona")
            .filter(evento_id=evento_id)
            .order_by("persona__nombres", "persona__apellidos")
        )
