"""
Constants — choices for domain models in usuarios module.
"""
from django.db import models


class TipoDocumentoChoices(models.TextChoices):
    """Tipos de documento de identidad reconocidos."""
    DNI = "DNI", "DNI"
    CE = "CE", "Carnet de Extranjería"
    PAS = "PAS", "Pasaporte"


class GeneroChoices(models.TextChoices):
    """Géneros reconocidos."""
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"