"""Resultados de los flujos de VALIDACIONES (DTOs de salida).

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §3

Son DTOs INTERNOS (Pydantic): no son schemas HTTP. El presenter los
transforma en el wrapper de la ruta.

`TicketPreviewResult` reproduce la forma congelada de `FR-05` §3.1 y
`TicketConfirmadoResult` la de `FR-05` §3.2.
"""

from datetime import datetime

from pydantic import BaseModel

from modules.validaciones.domain.ports.verificador_derecho import TitularDerecho


class TicketPreviewResult(BaseModel):
    """La vista previa de una credencial: lo que responde el dueño.

    NO consume, NO muta y NO escribe nada (`RN-P06`). Cuando `puede_canjear`
    es `False`, `motivo_codigo` y `motivo_mensaje` explican por qué: la prosa
    la publica el módulo dueño y es SEGURA.
    """

    tipo_derecho: str
    codigo: str
    titular: TitularDerecho
    edicion_id: str
    estado: str
    cantidad_total: int
    cantidad_disponible: int
    cantidad_consumida: int
    puede_canjear: bool
    motivo_codigo: str | None = None
    motivo_mensaje: str | None = None


class TicketConfirmadoResult(BaseModel):
    """El acta de un canje confirmado.

    `repetido` es `True` cuando la operación es la REPETICIÓN idempotente de
    una ejecución previa: no es un error, la primera ejecución y la
    repetición devuelven el MISMO `data` (`FR-05` §3.2).
    """

    validacion_id: str
    tipo_derecho: str
    cantidad_consumida: int
    cantidad_restante: int
    estado: str
    consumido_en: datetime
    actor_usuario_id: str | None = None
    actor_persona_id: str | None = None
    repetido: bool = False


__all__ = [
    "TicketConfirmadoResult",
    "TicketPreviewResult",
]
