"""
Constants — Choices and module-level constants for pagos.
"""
from django.db import models


class IzipayStatus(models.TextChoices):
    """Status choices for Izipay transaction attempts."""
    PENDIENTE = "PENDIENTE", "Pendiente"
    EXITO = "EXITO", "Exito"
    FALLIDO = "FALLIDO", "Fallido"
    CANCELADO = "CANCELADO", "Cancelado"
