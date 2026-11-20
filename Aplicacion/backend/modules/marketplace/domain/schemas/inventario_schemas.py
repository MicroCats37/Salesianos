"""DTOs internos del inventario de marketplace (`DOM-06`).

Contract: `contract/django-app-architecture-contract.md` §4.6

Son DTOs de Pydantic **puros** (no schemas HTTP). El wire no los ve: los
schemas HTTP viven en `presentation/schemas/`.

La CANTIDAD de un movimiento manual es **CON SIGNO** (`RN-M04`: "producto,
signo/cantidad, motivo, referencia origen y actor"): la naturaleza del
movimiento impone el signo y un ajuste declara el suyo.
"""

from pydantic import BaseModel, Field


class RegistrarMovimientoInventarioData(BaseModel):
    """El registro de un movimiento MANUAL de inventario (`FL-09`).

    Una salida sin venta NO crea compra ni pago (`RN-M05` · `QA-M02`): el
    movimiento es el único hecho que deja la operación.
    """

    producto_id: str = Field(..., description="Identificador del producto.")
    tipo: str = Field(
        ...,
        max_length=24,
        description="Naturaleza del movimiento (REPOSICION, MERMA, …).",
    )
    cantidad: int = Field(
        ...,
        description="Cantidad CON signo: positiva entra, negativa sale.",
    )
    motivo: str = Field(
        ...,
        max_length=200,
        description="Motivo del movimiento. Es obligatorio.",
    )


class RevertirMovimientoInventarioData(BaseModel):
    """La compensación de un movimiento ya registrado (`RN-M04`)."""

    movimiento_id: str = Field(..., description="Identificador del movimiento.")
    motivo: str = Field(
        ...,
        max_length=200,
        description="Motivo de la reversa.",
    )


class ConfirmarEntregaPedidoData(BaseModel):
    """La confirmación de la entrega de un pedido (`RN-M07`)."""

    pedido_id: str = Field(..., description="Identificador del pedido a entregar.")


__all__ = [
    "ConfirmarEntregaPedidoData",
    "RegistrarMovimientoInventarioData",
    "RevertirMovimientoInventarioData",
]
