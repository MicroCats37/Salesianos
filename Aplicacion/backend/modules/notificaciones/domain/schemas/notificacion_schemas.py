"""Schemas del módulo `notificaciones`.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Los schemas de este módulo son **internos**: el módulo no publica superficie
HTTP (no hay ruta en el ledger de FR-07 para las notificaciones, y `PD-08`
sigue abierto). El puerto `INotificadorCompraService` —que declara `pagos`— es
la frontera real, y su vocabulario vive en `modules/pagos/domain/schemas/`.
"""

from pydantic import BaseModel, ConfigDict, Field


class ResultadoEnvio(BaseModel):
    """El resultado de un intento de notificación, en vocabulario propio."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    enviada: bool = Field(
        default=False,
        description="Si el proveedor aceptó el envío.",
    )
    omitida: bool = Field(
        default=False,
        description="Si no se intentó enviar (no hay proveedor aprobado).",
    )
    recuperable: bool = Field(
        default=False,
        description="Si el intento admite un reintento.",
    )
    codigo: str = Field(default="", description="Código de máquina del resultado.")
    intentos: int = Field(default=0, description="Intentos consumidos.")
    registro_id: str | None = Field(
        default=None,
        description="Identificador del registro de trazabilidad.",
    )


__all__ = ["ResultadoEnvio"]
