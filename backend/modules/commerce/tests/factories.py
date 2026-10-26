"""Factories for commerce tests — pure dict builders (NOT pytest fixtures)."""
from decimal import Decimal


def make_compra_payload(
    responsable_id: str | None = None,
    descripcion: str = "Test purchase",
    referencia_externa: str = "TEST-REF-001",
    total: Decimal | str = "100.00",
    estado: str = "PENDIENTE",
    orden_pago_id: str | None = None,
    **kwargs,
) -> dict:
    """Build a commerce.Compra payload dict."""
    payload = {
        "descripcion": descripcion,
        "referencia_externa": referencia_externa,
        "total": str(total) if isinstance(total, Decimal) else total,
        "estado": estado,
    }
    if responsable_id is not None:
        payload["responsable_id"] = str(responsable_id)
    if orden_pago_id is not None:
        payload["orden_pago_id"] = str(orden_pago_id)
    return {**payload, **kwargs}


def make_orden_pago_payload(
    numero: str = "ORD-TEST-001",
    monto_total: Decimal | str = "100.00",
    moneda: str = "PEN",
    estado: str = "PENDIENTE",
    descripcion: str = "Test purchase",
    referencia_externa: str = "TEST-REF-001",
    metadata: dict | None = None,
    **kwargs,
) -> dict:
    """Build a pagos.OrdenPago payload dict."""
    payload = {
        "numero": numero,
        "monto_total": str(monto_total) if isinstance(monto_total, Decimal) else monto_total,
        "moneda": moneda,
        "estado": estado,
        "descripcion": descripcion,
        "referencia_externa": referencia_externa,
    }
    if metadata is not None:
        payload["metadata"] = metadata
    return {**payload, **kwargs}


def make_transaccion_pago_payload(
    orden_pago_id: str | None = None,
    amount: Decimal | str = "100.00",
    currency: str = "PEN",
    status: str = "CAPTURED",
    transaction_id: str = "TXN-TEST-001",
    order_number: str = "ORD-TEST-001",
    **kwargs,
) -> dict:
    """Build a pagos.TransaccionPago payload dict."""
    payload = {
        "amount": str(amount) if isinstance(amount, Decimal) else amount,
        "currency": currency,
        "status": status,
        "transaction_id": transaction_id,
        "order_number": order_number,
    }
    if orden_pago_id is not None:
        payload["orden_pago_id"] = str(orden_pago_id)
    return {**payload, **kwargs}


def make_compra_inscripcion_payload(
    compra_id: str | None = None,
    inscripcion_id: str | None = None,
    tipo: str = "INICIAL",
    cantidad: int = 10,
    precio_unitario: Decimal | str = "40.00",
    total: Decimal | str = "400.00",
    **kwargs,
) -> dict:
    """Build a salesianos_fest.CompraInscripcion payload dict."""
    payload = {
        "tipo": tipo,
        "cantidad": cantidad,
        "precio_unitario": str(precio_unitario) if isinstance(precio_unitario, Decimal) else precio_unitario,
        "total": str(total) if isinstance(total, Decimal) else total,
    }
    if compra_id is not None:
        payload["compra_id"] = str(compra_id)
    if inscripcion_id is not None:
        payload["inscripcion_id"] = str(inscripcion_id)
    return {**payload, **kwargs}
