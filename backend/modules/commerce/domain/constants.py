"""
Constants — Choices and module-level constants for commerce.
"""
from django.db import models


class EstadoCompraChoices(models.TextChoices):
    """Status choices for a generic commercial purchase (Compra)."""

    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA = "PAGADA", "Pagada"
    CANCELADA = "CANCELADA", "Cancelada"
