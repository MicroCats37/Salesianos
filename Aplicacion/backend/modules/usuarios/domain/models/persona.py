"""
`Persona` — identidad civil.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.1.

Invariantes congeladas:

- Clave natural ÚNICA `(tipo_documento, numero_documento)` con
  `UniqueConstraint` a nivel de base de datos.
- `numero_documento` se guarda NORMALIZADO (sin espacios ni separadores, en
  mayúsculas) y la comparación es case-insensitive por construcción.
- La `Persona` EXISTE SIN CUENTA: no exige `Usuario`.
- La misma `Persona` participa en ediciones distintas (`RN-U01`).
- El documento es un IDENTIFICADOR, no una credencial.

El modelo es plano y anémico (`contract/django-app-architecture-contract.md`
§6): campos, `Meta` y `__str__`. La lógica vive en los servicios.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from modules.usuarios.domain.constants import (
    GeneroChoices,
    OrigenDatosChoices,
    TipoDocumentoChoices,
)


class Persona(BaseModel):
    """Identidad civil de una persona, con o sin cuenta asociada."""

    history = HistoricalRecords()

    nombres = models.CharField(
        max_length=255,
        verbose_name="Nombres",
    )
    apellidos = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Apellidos",
        help_text=(
            "Apellidos de la persona. Puede ir vacío cuando la fuente externa "
            "no permite separar el nombre completo de forma fiable."
        ),
    )
    tipo_documento = models.CharField(
        max_length=3,
        choices=TipoDocumentoChoices.choices,
        verbose_name="Tipo de documento",
    )
    numero_documento = models.CharField(
        max_length=20,
        verbose_name="Número de documento",
        help_text="Documento normalizado: sin espacios ni separadores, en mayúsculas.",
    )
    genero = models.CharField(
        max_length=1,
        choices=GeneroChoices.choices,
        blank=True,
        default="",
        verbose_name="Género",
    )
    telefono = models.CharField(
        max_length=9,
        blank=True,
        default="",
        verbose_name="Teléfono",
    )
    whatsapp = models.CharField(
        max_length=9,
        blank=True,
        default="",
        verbose_name="WhatsApp",
    )
    contacto_emergencia_nombre = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Nombre de contacto de emergencia",
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=9,
        blank=True,
        default="",
        verbose_name="Teléfono de emergencia",
    )
    origen_datos = models.CharField(
        max_length=8,
        choices=OrigenDatosChoices.choices,
        default=OrigenDatosChoices.LOCAL,
        verbose_name="Origen de los datos",
        help_text=(
            "Procedencia de los datos de la persona. Se conserva para el "
            "control de calidad de la fuente externa (FR-03 §3.2 regla 5)."
        ),
    )
    datos_obtenidos_en = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de obtención de los datos",
        help_text="Instante en que la fuente externa entregó los datos.",
    )

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="unique_tipo_numero_documento",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombres} {self.apellidos} ({self.numero_documento})".strip()
