"""
Constants — Choices and module-level constants for inscripciones.
"""
from django.db import models


class ColegioChoices(models.TextChoices):
    """Choices for school/college affiliation."""
    SJB = "sjb", "San José"
    MA = "ma", "María Auxiliadora"


class EstadoInscripcionChoices(models.TextChoices):
    RECIBIDA = "RECIBIDA", "Recibida"
    EN_REVISION = "EN_REVISION", "En revision"
    OBSERVADA = "OBSERVADA", "Observada"
    VALIDADA = "VALIDADA", "Validada"
    PAGO_PENDIENTE = "PAGO_PENDIENTE", "Pago pendiente"
    PAGADA = "PAGADA", "Pagada"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    RECHAZADA = "RECHAZADA", "Rechazada"


class ModalidadChoices(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    MIXTO = "X", "Mixto"


class RolParticipanteChoices(models.TextChoices):
    JUGADOR = "JUGADOR", "Jugador"
    CAPITAN = "CAPITAN", "Capitan"
    DELEGADO = "DELEGADO", "Delegado"


class TalleCamisetaChoices(models.TextChoices):
    XS = "XS", "XS"
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"
    XXL = "XXL", "XXL"


class ModoDisciplinasPaqueteChoices(models.TextChoices):
    """
    Modo de selección de disciplinas para un paquete.

    FIJO: El paquete tiene disciplinas predefinidas y fijas (no se puede elegir).
    ELEGIBLE: El usuario puede elegir entre las disciplinas permitidas del paquete.
    """
    FIJO = "FIJO", "Fijo"
    ELEGIBLE = "ELEGIBLE", "Elegible"
