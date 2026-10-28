"""
Pure payload builders of the manual payment approval (pagos).

They are FUNCTIONS that return `dict` payloads — never fixtures, never a
factory library (`contract/TEST_ARCHITECTURE_CONTRACT.md` §4).
"""


def make_orden_pago_payload(
    numero: str = "OP-MANUAL-001",
    monto_total: str = "400.00",
    moneda: str = "PEN",
) -> dict:
    """Return the payload of a pending payment order."""
    return {
        "numero": numero,
        "monto_total": monto_total,
        "moneda": moneda,
    }


def make_payload_aprobacion_manual(
    canal: str = "TRANSFERENCIA_BANCARIA",
    referencia: str = "OP-123",
    monto: str = "400.00",
    moneda: str = "PEN",
    motivo: str = "Abono verificado en la cuenta de la institución",
) -> dict:
    """Return the payload of the administrative approval of a manual payment."""
    return {
        "canal": canal,
        "referencia": referencia,
        "monto": monto,
        "moneda": moneda,
        "motivo": motivo,
    }


def make_payload_anulacion_manual(
    motivo: str = "Registro administrativo duplicado",
) -> dict:
    """Return the payload of the administrative annulment of an approval."""
    return {"motivo": motivo}


__all__ = [
    "make_orden_pago_payload",
    "make_payload_aprobacion_manual",
    "make_payload_anulacion_manual",
]
