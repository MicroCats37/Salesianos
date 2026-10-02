"""
Domain schemas for pagos module — internal DTOs used by services, not HTTP.
"""
from pydantic import BaseModel, Field
from decimal import Decimal


class IzipayTransaccionCreateData(BaseModel):
    """Data needed to create an Izipay transaction record."""
    inscripcion_id: str
    transaction_id: str
    order_number: str
    amount: Decimal
    currency: str = "PEN"


class IzipayTransaccionUpdateData(BaseModel):
    """Data for updating an existing transaction."""
    status: str | None = None
    response_code: str | None = None
    response_message: str | None = None
    metodo_pago: str | None = None
    metadata: dict | None = None


class IzipayPrepareData(BaseModel):
    """Internal DTO for prepare step output (from orchestrator to controller)."""
    transaction_id: str
    order_number: str
    amount: Decimal
    currency: str
    inscripcion_id: str


class IzipayConfirmData(BaseModel):
    """Internal DTO for confirm step input."""
    transaction_id: str
    provider_status: str | None = None
    provider_response: dict | None = None
