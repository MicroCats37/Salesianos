"""Excepciones de dominio del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §10 (Exceptions)

Cada excepción declara un `code` ESTABLE y legible por máquina. El mensaje
público lo decide el catálogo de `core/exceptions.py` (A0) a partir de ese
código: esta clase NUNCA construye prosa para el usuario ni interpola UUIDs,
identificadores internos, rutas de disco ni texto crudo.

Los códigos de MEDIA (`MEDIA_TIPO_NO_PERMITIDO`, `MEDIA_TAMANO_EXCEDIDO`,
`MEDIA_TOKEN_NO_RESUELTO`, `MEDIA_ARCHIVO_HUERFANO`, `MEDIA_TOKEN_DUPLICADO`,
`MEDIA_DIMENSIONES_INVALIDAS`) YA están en el catálogo público de A0: los usa
`core.media` y este módulo NO los redefine.

Los códigos propios de este módulo todavía NO están en el catálogo público: se
registran como petición explícita a A0 (petición A0-03 del evidence de DOM-08).
Hasta que A0 los catalogue, el `error.code` sigue siendo estable y la prosa
pública cae al mensaje genérico del status (F-21).
"""

from core.exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)


class PatrocinadorNoEncontradoError(NotFoundError):
    """El patrocinador solicitado no existe dentro del alcance de edición."""

    code = "PATROCINADOR_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Patrocinador", code=self.code)


class PatrocinadorSlugDuplicadoError(ConflictError):
    """Ya existe un patrocinador con el mismo slug dentro de la misma edición."""

    code = "PATROCINADOR_SLUG_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="Ya existe un patrocinador con ese identificador en la edición.",
            code=self.code,
        )


class PatrocinadorImagenNoEncontradaError(NotFoundError):
    """La imagen indicada no pertenece al patrocinador del alcance."""

    code = "PATROCINADOR_IMAGEN_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Imagen de patrocinador", code=self.code)


class GaleriaPatrocinadorInvalidaError(UnprocessableEntityError):
    """La galería no es coherente: más imágenes de las que admite la galería.

    Es una regla ESTRUCTURAL del recurso (FR-06 §2.4 admite `0..N` archivos,
    pero el carrusel tiene un tope declarado), no una política comercial. La
    comprobación ocurre en el DOMINIO, ANTES de escribir archivos, para que un
    rechazo no deje residuos en el volumen (FR-06 §2.5).
    """

    code = "GALERIA_PATROCINADOR_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La galería del patrocinador no es válida.",
            code=self.code,
        )


class ModuloNoHabilitadoError(ConflictError):
    """La edición no tiene habilitado el módulo lógico `patrocinadores` (RN-E02).

    El CÓDIGO es el congelado por FR-02 §2.5 (`MODULO_NO_HABILITADO`) y ya
    está en el catálogo público de A0. La clase vive aquí para que este
    módulo no importe la jerarquía de excepciones de otro dominio.
    """

    code = "MODULO_NO_HABILITADO"

    def __init__(self):
        super().__init__(
            message="Esta funcionalidad no está habilitada en la edición.",
            code=self.code,
        )


__all__ = [
    "GaleriaPatrocinadorInvalidaError",
    "ModuloNoHabilitadoError",
    "PatrocinadorImagenNoEncontradaError",
    "PatrocinadorNoEncontradoError",
    "PatrocinadorSlugDuplicadoError",
]
