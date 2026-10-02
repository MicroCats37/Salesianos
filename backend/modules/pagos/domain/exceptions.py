"""
Domain exceptions for pagos module.
"""


class IzipayError(Exception):
    """Base exception for Izipay module."""
    pass


class TransaccionDuplicadaError(IzipayError):
    """Raised when a duplicate transaction_id is detected."""
    pass
