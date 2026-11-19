"""Excepciones de dominio del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §10 (Exceptions) ·
          `contract/api-wrapper-presenter-contract.md` §8 (error boundary)

Cada excepción declara un `code` ESTABLE y machine-readable. El mensaje
público lo decide el catálogo de `core/exceptions.py` (A0) a partir de ese
código: esta clase NUNCA construye prosa para el usuario ni interpola UUIDs,
identificadores internos o texto crudo.

Los códigos de este módulo son los que congela FR-02 §2.2:

| Código | Status | Cuándo |
|---|---|---|
| `EDICION_NO_ENCONTRADA` | 404 | el `edicion_id` explícito no existe |
| `EDICION_NO_PUBLICADA` | 404 | la edición existe pero no está `PUBLICADA` |
| `EDICION_AMBIGUA` | 409 | hay más de una candidata |
| `EDICION_NO_RESUELTA` | 404 | no hay edición que resolver |

Los códigos añadidos por este módulo y que todavía NO están en el catálogo
público de A0 se registran como petición explícita en el evidence de FND-02
(A0-01): `EVENTO_NO_ENCONTRADO`, `EDICION_SLUG_DUPLICADO`,
`EDICION_PUBLICADA_DUPLICADA`, `MODULO_NO_HABILITADO`.
"""

from core.exceptions import ConflictError, NotFoundError


class EventoNoEncontradoError(NotFoundError):
    """El evento indicado no existe."""

    code = "EVENTO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Evento", code=self.code)


class EdicionNoEncontradaError(NotFoundError):
    """El `edicion_id` explícito no corresponde a ninguna edición (FR-02 §2.2 #1)."""

    code = "EDICION_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Edición", code=self.code)


class EdicionNoPublicadaError(NotFoundError):
    """La edición existe pero su estado no es `PUBLICADA` (FR-02 §2.6)."""

    code = "EDICION_NO_PUBLICADA"

    def __init__(self):
        super().__init__(resource="Edición", code=self.code)


class EdicionNoResueltaError(NotFoundError):
    """No hay ninguna edición que resuelva el alcance pedido (FR-02 §2.2 #4)."""

    code = "EDICION_NO_RESUELTA"

    def __init__(self):
        super().__init__(resource="Edición", code=self.code)


class EdicionAmbiguaError(ConflictError):
    """Hay más de una edición candidata: nunca se elige una por defecto (FR-02 §2.2)."""

    code = "EDICION_AMBIGUA"

    def __init__(self, candidatas=None):
        #: Candidatas en conflicto. Contenido PÚBLICO SEGURO: slug, nombre y
        #: año. Nunca UUIDs, ids internos ni texto de excepción.
        self.candidatas = list(candidatas or [])
        super().__init__(
            message="Hay más de una edición posible para el alcance solicitado.",
            code=self.code,
        )


class EdicionSlugDuplicadoError(ConflictError):
    """Ya existe una edición con el mismo slug dentro del mismo evento."""

    code = "EDICION_SLUG_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="Ya existe una edición con ese identificador en el evento.",
            code=self.code,
        )


class EdicionPublicadaDuplicadaError(ConflictError):
    """El evento ya tiene una edición `PUBLICADA` (invariante FR-02 §3).

    Es la traducción de dominio de la violación de la `UniqueConstraint`
    condicional: la base de datos es la autoridad final y dos publicaciones
    simultáneas no pueden coexistir.
    """

    code = "EDICION_PUBLICADA_DUPLICADA"

    def __init__(self):
        super().__init__(
            message="El evento ya tiene una edición publicada.",
            code=self.code,
        )


class ModuloNoHabilitadoError(ConflictError):
    """La edición no tiene habilitado el módulo lógico requerido (RN-E02)."""

    code = "MODULO_NO_HABILITADO"

    def __init__(self):
        super().__init__(
            message="Esta funcionalidad no está habilitada en la edición.",
            code=self.code,
        )


__all__ = [
    "EdicionAmbiguaError",
    "EdicionNoEncontradaError",
    "EdicionNoPublicadaError",
    "EdicionNoResueltaError",
    "EdicionPublicadaDuplicadaError",
    "EdicionSlugDuplicadoError",
    "EventoNoEncontradoError",
    "ModuloNoHabilitadoError",
]
