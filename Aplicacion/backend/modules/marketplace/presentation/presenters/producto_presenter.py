"""Presenters del módulo `marketplace` — result de dominio → schema HTTP.

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

Los presenters son TRANSFORMADORES PUROS: reciben un result object y
devuelven un schema HTTP. No consultan la base de datos, no llaman a
selectores y no construyen mensajes públicos de error.

Cada presenter tiene UN método público, el de su endpoint (FR-07 §4). Los
nombres de los presenters son los que declara el ledger ruta → wrapper
(FR-07 §3.3): `ProductoPresenter`, `ProductoListaPresenter`,
`ProductoDetallePresenter` y `CategoriaListaPresenter`.
"""

from modules.marketplace.domain.results.producto_result import (
    CategoriaProductoResult,
    ProductoListItemResult,
    ProductoResult,
)
from modules.marketplace.presentation.schemas.producto_schemas import (
    CategoriaListaOut,
    ProductoDetalleOut,
    ProductoImagenOut,
    ProductoListItemOut,
    ProductoOut,
)


class ProductoPresenter:
    """Presenter de `RT-MD-01` (alta de producto)."""

    @staticmethod
    def present(result: ProductoResult) -> ProductoOut:
        """Proyecta el result de un producto al wrapper HTTP."""
        return ProductoOut(
            id=result.id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            categoria_id=result.categoria_id,
            categoria_nombre=result.categoria_nombre,
            nombre=result.nombre,
            slug=result.slug,
            descripcion=result.descripcion,
            precio=result.precio,
            precio_oferta=result.precio_oferta,
            precio_efectivo=result.precio_efectivo,
            oferta_activa=result.oferta_activa,
            oferta_inicia=result.oferta_inicia,
            oferta_termina=result.oferta_termina,
            estado=result.estado,
            imagenes=[ProductoPresenter.present_imagen(imagen) for imagen in result.imagenes],
            imagen_principal_url=result.imagen_principal_url,
        )

    @staticmethod
    def present_imagen(imagen) -> ProductoImagenOut:
        """Proyecta una imagen de la galería al wrapper HTTP."""
        return ProductoImagenOut(
            id=imagen.id,
            orden=imagen.orden,
            url=imagen.url,
            es_principal=imagen.es_principal,
            texto_alternativo=imagen.texto_alternativo,
            disponible=imagen.disponible,
            created_at=imagen.created_at,
        )


class ProductoListaPresenter:
    """Presenter de `RT-MK-02` (listado del catálogo)."""

    @staticmethod
    def present_lista(items: list[ProductoListItemResult]) -> list[ProductoListItemOut]:
        """Proyecta la lista de productos del catálogo."""
        return [
            ProductoListItemOut(
                id=item.id,
                nombre=item.nombre,
                slug=item.slug,
                categoria_id=item.categoria_id,
                categoria_nombre=item.categoria_nombre,
                precio=item.precio,
                precio_oferta=item.precio_oferta,
                precio_efectivo=item.precio_efectivo,
                oferta_activa=item.oferta_activa,
                estado=item.estado,
                imagen_principal_url=item.imagen_principal_url,
                cantidad_imagenes=item.cantidad_imagenes,
            )
            for item in items
        ]


class ProductoDetallePresenter:
    """Presenter de `RT-MK-03` (detalle de un producto)."""

    @staticmethod
    def present_detalle(result: ProductoResult) -> ProductoDetalleOut:
        """Proyecta el result del producto con su galería ordenada."""
        return ProductoDetalleOut(
            **ProductoPresenter.present(result).model_dump(),
        )


class CategoriaListaPresenter:
    """Presenter de `RT-MK-01` (listado de categorías)."""

    @staticmethod
    def present_categorias(items: list[CategoriaProductoResult]) -> list[CategoriaListaOut]:
        """Proyecta la lista de categorías del catálogo."""
        return [
            CategoriaListaOut(
                id=item.id,
                nombre=item.nombre,
                slug=item.slug,
                orden=item.orden,
            )
            for item in items
        ]


__all__ = [
    "CategoriaListaPresenter",
    "ProductoDetallePresenter",
    "ProductoListaPresenter",
    "ProductoPresenter",
]
