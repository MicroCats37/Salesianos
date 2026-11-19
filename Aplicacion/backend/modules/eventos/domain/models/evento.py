"""`Evento` — la familia de evento (no es un alcance de datos).

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

`Evento` agrupa ediciones. NO es un scope de datos: la unidad de alcance es
`Edicion` (FR-02 §2.1 — "`Edicion` es la unidad de scope. `Evento` es la
familia que agrupa ediciones y **no** es un scope de datos").

Sobre el modelo congelado (`backend/modules/eventos/domain/models/evento.py`)
este modelo difiere de forma DELIBERADA y trazable:

| Campo congelado | Decisión en el objetivo | Motivo |
|---|---|---|
| `nombre` | se conserva | identidad visible de la familia |
| `fecha_inicio` / `fecha_fin` | **se elimina** de `Evento` | el calendario pertenece a la EDICIÓN (FR-02 §3); en `Evento` duplicaría el dato y crearía dos fuentes de verdad |
| `esta_activo` | **se elimina** | es exactamente el supuesto de "evento activo global" que FR-02 §2 reemplaza; la unicidad de la edición publicada la garantiza la `UniqueConstraint` condicional |
| `fecha_limite_modificacion` | **se elimina** | no existe en el plan ratified; GOV-01-OPEN-03 deja el ciclo de vida de la edición pendiente |
| — | `slug` se añade | FR-02 §2.1 exige `slug`; es la forma de resolver por identificador estable en el borde de entrada (§2.3 #2) |

El modelo es plano y anémico: sólo campos, `Meta` y `__str__`. Toda la
lógica vive en los servicios del módulo (§6 del contrato de arquitectura).
"""

from django.db import models

from core.models import BaseModel


class Evento(BaseModel):
    """Familia de evento. Agrupa ediciones; no es un alcance de datos."""

    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del evento",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Identificador del evento",
        help_text="Identificador estable y único del evento dentro del sistema.",
    )

    class Meta:
        db_table = "eventos_evento"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre
