"""Excepciones de dominio del módulo `marketplace`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §10 (Exceptions)

Cada excepción declara un `code` ESTABLE y machine-readable. El mensaje
público lo decide el catálogo de `core/exceptions.py` (A0) a partir de ese
código: esta clase NUNCA construye prosa para el usuario ni interpola UUIDs,
identificadores internos, rutas de disco ni texto crudo.

Los códigos de MEDIA (`MEDIA_TIPO_NO_PERMITIDO`, `MEDIA_TAMANO_EXCEDIDO`,
`MEDIA_TOKEN_NO_RESUELTO`, `MEDIA_ARCHIVO_HUERFANO`, `MEDIA_TOKEN_DUPLICADO`,
`MEDIA_DIMENSIONES_INVALIDAS`) YA están en el catálogo público de A0: los usa
`core.media` y este módulo NO los redefine.

Los códigos de este módulo que todavía NO están en el catálogo público se
registran como petición explícita a A0 (petición A0-01 del evidence de
DOM-04). Hasta que A0 los catalogue, el `error.code` sigue siendo estable y
la prosa pública cae al mensaje genérico del status (F-21).
"""

from core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)


class ProductoNoEncontradoError(NotFoundError):
    """El producto solicitado no existe dentro del alcance de edición."""

    code = "PRODUCTO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Producto", code=self.code)


class ProductoSlugDuplicadoError(ConflictError):
    """Ya existe un producto con el mismo slug dentro de la misma edición."""

    code = "PRODUCTO_SLUG_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="Ya existe un producto con ese identificador en la edición.",
            code=self.code,
        )


class ProductoNoDisponibleError(ConflictError):
    """El producto no está disponible para la operación solicitada.

    Lo consume `RT-CM-03` (pedido, DOM-05) y la operación de stock
    (DOM-06). En DOM-04 el código queda declarado, pero la comprobación de
    existencias es de esos paquetes: este módulo NO inventa stock.
    """

    code = "PRODUCTO_NO_DISPONIBLE"

    def __init__(self):
        super().__init__(
            message="El producto seleccionado no está disponible.",
            code=self.code,
        )


class ProductoCategoriaIncoherenteError(UnprocessableEntityError):
    """La categoría indicada pertenece a OTRA edición que el producto.

    La coherencia de edición (FR-02 §3 · RN-E01) es estructural: un producto
    y su categoría tienen que vivir en el MISMO alcance.
    """

    code = "PRODUCTO_CATEGORIA_INCOHERENTE"

    def __init__(self):
        super().__init__(
            message="La categoría indicada pertenece a otra edición.",
            code=self.code,
        )


class CategoriaProductoNoEncontradaError(NotFoundError):
    """La categoría de producto solicitada no existe en el alcance."""

    code = "CATEGORIA_PRODUCTO_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Categoría de producto", code=self.code)


class CategoriaProductoSlugDuplicadoError(ConflictError):
    """Ya existe una categoría con el mismo slug dentro de la misma edición."""

    code = "CATEGORIA_PRODUCTO_SLUG_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="Ya existe una categoría con ese identificador en la edición.",
            code=self.code,
        )


class ProductoImagenNoEncontradaError(NotFoundError):
    """La imagen indicada no pertenece al producto del alcance."""

    code = "PRODUCTO_IMAGEN_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Imagen de producto", code=self.code)


class OfertaInvalidaError(UnprocessableEntityError):
    """La oferta no es coherente: precio negativo o ventana invertida.

    Es una regla ESTRUCTURAL (coherencia del dato), no una política comercial:
    la política de precios y ofertas es de A5 + producto.
    """

    code = "OFERTA_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La oferta indicada no es válida.",
            code=self.code,
        )


class GaleriaInvalidaError(UnprocessableEntityError):
    """La galería no es coherente: más de una imagen principal.

    FR-06 §2.6: la imagen principal es un campo EXPLÍCITO y la base de
    datos admite como máximo UNA por producto. La comprobación ocurre en el
    dominio, ANTES de escribir archivos, para que un rechazo no deje
    residuos en el volumen (FR-06 §2.5).
    """

    code = "GALERIA_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La galería del producto no es válida.",
            code=self.code,
        )


class ModuloNoHabilitadoError(ConflictError):
    """La edición no tiene habilitado el módulo lógico `marketplace` (RN-E02).

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


# ── Pedido de marketplace (DOM-05) ───────────────────────────────────────────
#
# Los códigos de esta familia todavía NO están en el catálogo público de A0:
# se registran como petición explícita (A0-01 del evidence de DOM-05). Hasta
# que A0 los catalogue, el `error.code` sigue siendo estable y la prosa
# pública cae al mensaje genérico del status (F-21).


class PedidoNoEncontradoError(NotFoundError):
    """El pedido solicitado no existe dentro del alcance.

    La denegación es NEUTRAL: un token desconocido y un pedido de otra persona
    se responden igual (RB-02 · SHOP-03).
    """

    code = "PEDIDO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Pedido", code=self.code)


class PedidoNoAutorizadoError(ForbiddenError):
    """El actor autenticado NO es el comprador del pedido.

    Ser administrador NO sustituye la titularidad (RN-U02, FR-03 §2.1).

    El CÓDIGO es propio del módulo: `ForbiddenError` deja `ACTION_NOT_ALLOWED`
    como código por defecto y esta clase lo sustituye por uno estable y
    legible por máquina. La prosa pública la decide el catálogo de A0 (petición
    A0-01 del evidence de DOM-05).
    """

    code = "PEDIDO_NO_AUTORIZADO"

    def __init__(self):
        super().__init__(
            message="No tienes autorización para consultar este pedido.",
        )


class PedidoItemsMixtosError(UnprocessableEntityError):
    """El pedido mezcla artículos de DISTINTOS orígenes.

    RN-C01: no existe un carrito combinado. Un pedido de tienda no puede
    mezclar un pase, una inscripción y un producto.
    """

    code = "PEDIDO_ITEMS_MIXTOS"

    def __init__(self):
        super().__init__(
            message="No se pueden combinar artículos de distintos orígenes.",
            code=self.code,
        )


class PedidoItemNoPermitidoError(ConflictError):
    """El pedido declara un artículo que NO pertenece a la tienda.

    Un pase o una inscripción se compran por su propio endpoint y su propio
    flujo (RN-C01, DEC-10): nunca dentro de un pedido de marketplace.
    """

    code = "PEDIDO_ITEM_NO_PERMITIDO"

    def __init__(self):
        super().__init__(
            message="El pedido sólo puede incluir productos de la tienda.",
            code=self.code,
        )


class PedidoCantidadInvalidaError(UnprocessableEntityError):
    """La cantidad declarada de un artículo no es válida.

    La cantidad se valida en el servidor: cero o un tope por encima del
    máximo admitido.
    """

    code = "PEDIDO_CANTIDAD_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La cantidad solicitada no es válida.",
            code=self.code,
        )


class CompradorSinPersonaError(UnprocessableEntityError):
    """La cuenta autenticada no tiene una persona vinculada.

    El CÓDIGO es el congelado por DOM-01 (`COMPRADOR_SIN_PERSONA`) y ya está
    en el catálogo público de A0: este módulo lo reutiliza y no lo redefine.
    """

    code = "COMPRADOR_SIN_PERSONA"

    def __init__(self):
        super().__init__(
            message="La cuenta no tiene una persona vinculada.",
            code=self.code,
        )


__all__ = [
    "CategoriaProductoNoEncontradaError",
    "CategoriaProductoSlugDuplicadoError",
    "CompradorSinPersonaError",
    "GaleriaInvalidaError",
    "ModuloNoHabilitadoError",
    "OfertaInvalidaError",
    "PedidoCantidadInvalidaError",
    "PedidoItemNoPermitidoError",
    "PedidoItemsMixtosError",
    "PedidoNoAutorizadoError",
    "PedidoNoEncontradoError",
    "ProductoCategoriaIncoherenteError",
    "ProductoImagenNoEncontradaError",
    "ProductoNoDisponibleError",
    "ProductoNoEncontradoError",
    "ProductoSlugDuplicadoError",
]
