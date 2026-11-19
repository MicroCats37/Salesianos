"""Result objects del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.6
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompraResult(BaseModel):
    """Estado de una compra comercial.

    `reutilizada` dice si esta llamada creó la compra o si encontró la
    compra pendiente de la misma intención (FR-04 I-4).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="Identificador de la compra.")
    persona_id: str = Field(..., description="Identificador de la persona compradora.")
    origen: str = Field(..., description="Dominio de origen de la compra.")
    estado: str = Field(..., description="Estado comercial de la compra.")
    total: Decimal = Field(..., description="Total congelado de la compra.")
    moneda: str = Field(..., description="Código ISO-4217 del total.")
    lineas_snapshot: list = Field(
        default_factory=list,
        description="Snapshot inmutable de lo comprado.",
    )
    orden_pago_id: str | None = Field(
        default=None,
        description="Orden de pago que financia la compra.",
    )
    referencia: str = Field(..., description="Referencia de la intención de compra.")
    creada_en: datetime = Field(..., description="Instante de creación de la compra.")
    reutilizada: bool = Field(
        default=False,
        description="Si la compra ya existía y se reutilizó.",
    )


__all__ = ["CompraResult"]
