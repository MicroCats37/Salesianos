"""Base abstracta de los modelos del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Añade a `core.models.BaseModel` (UUID + marcas de tiempo) el CONTADOR DE
VERSIÓN que usan las operaciones con bloqueo optimista:

    version: se incrementa en cada escritura. El cliente viaja la versión que
    conoce (`expected_version`) y el servidor la compara: si ya no es la
    actual, la operación se rechaza con `RESOURCE_CHANGED` (409) y NO se
    escribe nada (`frontend/05` §5, `QA-K05`).

El modelo es ANÉMICO (`contract/django-app-architecture-contract.md` §6):
campos, `Meta` y `__str__`. Toda la lógica vive en los servicios.
"""

from django.db import models

from core.models import BaseModel


class CompetenciaBaseModel(BaseModel):
    """Base abstracta de `Competencia`, `CompetenciaEquipo`, `Ronda` y `Encuentro`."""

    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Versión",
        help_text=(
            "Contador de bloqueo optimista. El cliente envía la versión que "
            "conoce y el servidor la compara antes de escribir."
        ),
    )

    class Meta:
        abstract = True


__all__ = ["CompetenciaBaseModel"]
