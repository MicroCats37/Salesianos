"""
Persona — natural person with identity data for Salesianos FEST.

Represents a participant/responsible with civil identity information.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import TipoDocumentoChoices, GeneroChoices


class Persona(BaseModel):
    """
    Natural person with civil identity data.

    A Persona is associated with a Usuario for system authentication,
    and contains the civil identity information for the Salesianos FEST event.
    """

    tipos_documento = TipoDocumentoChoices
    generos = GeneroChoices
    history = HistoricalRecords()

    nombres = models.CharField(
        max_length=255,
        verbose_name="Nombres"
    )
    apellidos = models.CharField(
        max_length=255,
        verbose_name="Apellidos"
    )
    tipo_documento = models.CharField(
        max_length=3,
        choices=tipos_documento.choices,
        verbose_name="Tipo de documento"
    )
    numero_documento = models.CharField(
        max_length=20,
        verbose_name="Número de documento"
    )
    genero = models.CharField(
        max_length=1,
        choices=generos.choices,
        verbose_name="Género"
    )
    telefono = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    whatsapp = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="WhatsApp"
    )
    contacto_emergencia_nombre = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Nombre de contacto de emergencia"
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="Teléfono de emergencia"
    )
    aseguradora_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre de aseguradora"
    )
    aseguradora_numero_poliza = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de póliza"
    )
    acepto_bases = models.BooleanField(
        default=False,
        verbose_name="Aceptó bases del evento"
    )
    acepto_aptitud_fisica = models.BooleanField(
        default=False,
        verbose_name="Aceptó certificado de aptitud física"
    )
    acepto_imagen = models.BooleanField(
        default=False,
        verbose_name="Aceptó uso de imagen"
    )

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="unique_tipo_numero_documento"
            )
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.numero_documento})"
