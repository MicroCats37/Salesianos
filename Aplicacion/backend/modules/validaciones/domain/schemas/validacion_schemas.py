"""Schemas INTERNOS de VALIDACIONES (DTOs de entrada del dominio).

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0`

No son schemas HTTP: son los datos que el flujo necesita, con la forma que
necesita (`contract/django-app-architecture-contract.md` §4.6).

La CANTIDAD confirmada la pide el operador. `None` significa "todo lo
disponible": el flujo lo resuelve contra el dueño, nunca el navegador
(`FR-05` §2.2).
"""

from pydantic import BaseModel, Field


class PreviewTicketData(BaseModel):
    """La petición de una vista previa.

    `codigo` es la CREDENCIAL. Es un secreto: viaja en el cuerpo de la
    petición y no se registra en la auditoría.
    """

    codigo: str = Field(..., min_length=1, max_length=64)
    edicion_id: str | None = Field(default=None)


class ConfirmarTicketData(BaseModel):
    """La petición de una confirmación.

    `idempotency_key` es OBLIGATORIA (`FR-04` §2.2): identifica UNA
    intención. Una repetición devuelve el resultado de la primera ejecución.

    `cantidad` es la cantidad que el operador pide consumir. `None` significa
    "todo lo disponible".
    """

    codigo: str = Field(..., min_length=1, max_length=64)
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    cantidad: int | None = Field(default=None, ge=1)
    edicion_id: str | None = Field(default=None)


__all__ = [
    "ConfirmarTicketData",
    "PreviewTicketData",
]
