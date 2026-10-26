"""
Test doubles for the payment-order ownership port.

Pure Python classes — no pytest, no DB. They record the calls they receive so
the tests can assert that the flow really asks who owns the order before it
accepts a browser relay.
"""
from modules.pagos.domain.ports import IPropietarioOrdenPagoService


class PropietarioOrdenPagoFake(IPropietarioOrdenPagoService):
    """
    In-memory double for IPropietarioOrdenPagoService.

    Args:
        propietarios: when given, only those person ids own the order.
        por_defecto: what the port answers for anybody else (default: owns).
    """

    def __init__(
        self,
        propietarios: set[str] | None = None,
        por_defecto: bool = True,
    ):
        self.propietarios = set(propietarios) if propietarios else None
        self.por_defecto = por_defecto
        self.llamadas: list[tuple[str, str]] = []

    def es_propietario(self, orden_pago_id: str, persona_id: str) -> bool:
        """Record the call and answer with the configured ownership."""
        self.llamadas.append((orden_pago_id, persona_id))
        if self.propietarios is not None:
            return persona_id in self.propietarios
        return self.por_defecto

    @property
    def llamada_actual(self) -> tuple[str, str] | None:
        """The last (orden_pago_id, persona_id) received, or None."""
        return self.llamadas[-1] if self.llamadas else None


__all__ = ["PropietarioOrdenPagoFake"]
