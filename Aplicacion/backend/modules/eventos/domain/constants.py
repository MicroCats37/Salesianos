"""Vocabulario cerrado del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`

Dos vocabularios cerrados:

1. `EstadoEdicion` — el estado de ciclo de vida de una edición
   (FR-02 §2.1). La lista es CERRADA: `BORRADOR`, `PUBLICADA`, `CERRADA`.
2. `ModuloLogico` — las funcionalidades opcionales que una edición puede
   habilitar (FR-02 §2.5, regla de negocio `RN-E02`).

Sobre `ModuloLogico` hay TRES reglas congeladas que este módulo respeta:

- El valor por defecto de cada módulo es **deshabilitado**. Una edición
  nace sin módulos habilitados; habilitarlos es una decisión explícita.
- La habilitación es **dato de configuración de la edición**, no un flag de
  despliegue: vive en `Edicion.modulos_habilitados`.
- Un módulo no habilitado no expone catálogo ni rutas de escritura.

Este archivo NO declara el nombre del evento activo: la resolución de
edición es un orden único y vive en
`modules/eventos/domain/services/core/edicion_scope_service.py`
(FR-02 §2.2). No existe ninguna constante de "edición activa" en settings.
"""

from django.db import models


class EstadoEdicion(models.TextChoices):
    """Estado de ciclo de vida de una edición (FR-02 §2.1)."""

    BORRADOR = "BORRADOR", "Borrador"
    PUBLICADA = "PUBLICADA", "Publicada"
    CERRADA = "CERRADA", "Cerrada"


class ModuloLogico(models.TextChoices):
    """Funcionalidades opcionales habilitables por edición (FR-02 §2.5)."""

    INSCRIPCIONES = "inscripciones", "Inscripciones deportivas"
    PASES = "pases", "Pases / beneficios"
    MARKETPLACE = "marketplace", "Marketplace"
    COMPETENCIAS = "competencias", "Competencias"
    PATROCINADORES = "patrocinadores", "Patrocinadores"


#: Claves habilitables, en el orden estable en que se exponen al cliente.
MODULOS_HABILITABLES: tuple[str, ...] = tuple(ModuloLogico.values)

__all__ = [
    "MODULOS_HABILITABLES",
    "EstadoEdicion",
    "ModuloLogico",
]
