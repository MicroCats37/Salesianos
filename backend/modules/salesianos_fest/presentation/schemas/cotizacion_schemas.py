"""HTTP schemas for quotation endpoint."""
from datetime import datetime
from typing import Optional

from core.types import BaseSchema


class CotizacionRequest(BaseSchema):
    """Request schema for POST /api/cotizaciones/."""

    paquete_id: str
    cantidad: int


class CotizacionResponse(BaseSchema):
    """Response schema for quotation — stateless calculation.

    The quotation is NOT persisted; it is a pure calculation based on the
    current catalog state. The client stores it in form state and sends it
    back at confirmation time for server-side revalidation.

    The `version` field reflects the current price version; if the catalog
    changes between quotation and confirmation, the server will detect the
    mismatch and return a PRECIO_CAMBIO conflict.
    """

    paquete_id: str
    paquete_nombre: str
    modo_disciplinas: str
    minimo_cantidad: int  # Paquete.minimo_compra_inicial
    cantidad_cotizada: int
    precio_unitario: float
    precio_regular: float
    precio_preventa: Optional[float]
    total: float
    validez_hasta: datetime
    version: int  # price version counter
    estado: str  # ACTIVA | EXPIRADA
