"""`ProductoCoreService` — escritura y proyección del catálogo de productos.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.3 (core services)

El core service es SYNC y **NO abre `transaction.atomic()`**: la atomicidad
compuesta la aporta el flujo.

Reglas que este servicio es el dueño de:

- **Coherencia de edición** (FR-02 §3 · RN-E01): el producto y su categoría
  tienen que pertenecer a la MISMA edición.
- **Coherencia de la oferta** (RN-M02): precio no negativo y ventana de
  oferta no invertida. Es una regla ESTRUCTURAL del dato, no una política
  comercial.
- **Autoridad del precio**: `precio_efectivo` y `oferta_activa` los calcula
  aquí, en el DOMINIO. El cliente nunca los deriva.
"""

from decimal import Decimal

from modules.marketplace.domain.constants import EstadoProducto
from modules.marketplace.domain.exceptions import (
    GaleriaInvalidaError,
    OfertaInvalidaError,
    ProductoCategoriaIncoherenteError,
)
from modules.marketplace.domain.models import Producto
from modules.marketplace.domain.results.producto_result import (
    CategoriaProductoResult,
    ProductoImagenResult,
    ProductoListItemResult,
    ProductoResult,
)
from modules.marketplace.domain.schemas.producto_schemas import ProductoCreateData
from modules.marketplace.domain.selectors.categoria_selector import (
    CategoriaProductoSelector,
)
from modules.marketplace.domain.selectors.producto_selector import ProductoSelector
from modules.marketplace.domain.services.core.producto_media_service import (
    ProductoMediaService,
)


class ProductoCoreService:
    """Operaciones de escritura y proyección del catálogo de productos."""

    def __init__(
        self,
        categoria_selector: CategoriaProductoSelector = None,
        producto_selector: ProductoSelector = None,
        media_service: ProductoMediaService = None,
    ):
        self.categoria_selector = categoria_selector or CategoriaProductoSelector()
        self.producto_selector = producto_selector or ProductoSelector()
        self.media_service = media_service or ProductoMediaService()

    # ── Alta ────────────────────────────────────────────────────────────────

    def crear(self, data: ProductoCreateData) -> Producto:
        """Crea un producto dentro del alcance de edición indicado.

        La categoría, si se indica, tiene que pertenecer a la MISMA edición:
        la coherencia de edición es estructural y se comprueba aquí.
        """
        categoria = None
        if data.categoria_id is not None:
            categoria = self.categoria_selector.obtener_por_id(data.categoria_id)
            if categoria is None:
                from modules.marketplace.domain.exceptions import (
                    CategoriaProductoNoEncontradaError,
                )

                raise CategoriaProductoNoEncontradaError()
            if str(categoria.edicion_id) != str(data.edicion_id):
                raise ProductoCategoriaIncoherenteError()

        self.validar_oferta(
            precio=data.precio,
            precio_oferta=data.precio_oferta,
            oferta_inicia=data.oferta_inicia,
            oferta_termina=data.oferta_termina,
        )

        self.validar_galeria(data.imagenes or [])

        return Producto.objects.create(
            edicion_id=data.edicion_id,
            categoria=categoria,
            nombre=data.nombre,
            slug=data.slug,
            descripcion=data.descripcion or "",
            precio=data.precio,
            precio_oferta=data.precio_oferta,
            oferta_inicia=data.oferta_inicia,
            oferta_termina=data.oferta_termina,
            estado=data.estado or EstadoProducto.ACTIVO,
        )

    @staticmethod
    def validar_galeria(imagenes) -> None:
        """Coherencia de la galería antes de ESCRIBIR un solo archivo.

        La `UniqueConstraint` condicional de la base de datos es la
        autoridad final ("una sola imagen principal por producto"), pero
        comprobarla aquí evita escribir archivos que después habría que
        borrar (FR-06 §2.5).
        """
        principales = [imagen for imagen in imagenes if getattr(imagen, "es_principal", False)]
        if len(principales) > 1:
            raise GaleriaInvalidaError()

    def crear_categoria(self, data) -> object:
        """Crea una categoría de producto dentro de una edición."""
        from modules.marketplace.domain.models import CategoriaProducto

        return CategoriaProducto.objects.create(
            edicion_id=data.edicion_id,
            nombre=data.nombre,
            slug=data.slug,
            orden=data.orden,
        )

    def actualizar(self, producto: Producto, data) -> Producto:
        """Actualización parcial. NO toca la galería ni el alcance."""
        campos = data.model_dump(exclude_unset=True, exclude_none=True)
        for campo, valor in campos.items():
            setattr(producto, campo, valor)
        producto.save()
        return producto

    # ── Reglas de oferta ────────────────────────────────────────────────────

    @staticmethod
    def validar_oferta(
        *,
        precio: Decimal,
        precio_oferta: Decimal | None,
        oferta_inicia=None,
        oferta_termina=None,
    ) -> None:
        """Coherencia estructural del precio y de la ventana de oferta."""
        if precio is not None and precio < Decimal("0"):
            raise OfertaInvalidaError()
        if precio_oferta is not None and precio_oferta < Decimal("0"):
            raise OfertaInvalidaError()
        if (
            oferta_inicia is not None
            and oferta_termina is not None
            and oferta_termina <= oferta_inicia
        ):
            raise OfertaInvalidaError()

    # ── Proyección a results ────────────────────────────────────────────────

    def result_de(self, producto: Producto, imagenes=None, ahora=None) -> ProductoResult:
        """Proyecta un producto (con su galería) al result object."""
        if imagenes is None:
            imagenes = self.producto_selector.listar_imagenes(producto.id)
        imagenes_result = [self.result_imagen(imagen) for imagen in imagenes]
        principal = next(
            (imagen for imagen in imagenes_result if imagen.es_principal and imagen.url),
            None,
        )
        return ProductoResult(
            id=producto.id,
            edicion_id=producto.edicion_id,
            edicion_nombre=getattr(getattr(producto, "edicion", None), "nombre", "") or "",
            categoria_id=producto.categoria_id,
            categoria_nombre=getattr(getattr(producto, "categoria", None), "nombre", None),
            nombre=producto.nombre,
            slug=producto.slug,
            descripcion=producto.descripcion or "",
            precio=producto.precio,
            precio_oferta=producto.precio_oferta,
            precio_efectivo=producto.precio_efectivo(ahora),
            oferta_activa=producto.oferta_activa(ahora),
            oferta_inicia=producto.oferta_inicia,
            oferta_termina=producto.oferta_termina,
            estado=producto.estado,
            imagenes=imagenes_result,
            imagen_principal_url=principal.url if principal else None,
            created_at=producto.created_at,
            updated_at=producto.updated_at,
        )

    def result_imagen(self, imagen) -> ProductoImagenResult:
        """Proyecta una imagen al result object, degradando si falta el archivo."""
        ruta = imagen.imagen.name if imagen.imagen else ""
        disponible = self.media_service.disponible(ruta)
        return ProductoImagenResult(
            id=imagen.id,
            orden=imagen.orden,
            url=self.media_service.url_de(ruta) if disponible else None,
            es_principal=bool(imagen.es_principal),
            texto_alternativo=imagen.texto_alternativo or "",
            disponible=disponible,
            created_at=imagen.created_at,
        )

    def result_item(self, producto: Producto, imagenes=None, ahora=None) -> ProductoListItemResult:
        """Proyecta un producto al item de la lista del catálogo."""
        if imagenes is None:
            imagenes = self.producto_selector.listar_imagenes(producto.id)
        principal = next(
            (
                imagen
                for imagen in imagenes
                if imagen.es_principal and self.media_service.disponible(imagen.imagen.name)
            ),
            None,
        )
        return ProductoListItemResult(
            id=producto.id,
            nombre=producto.nombre,
            slug=producto.slug,
            categoria_id=producto.categoria_id,
            categoria_nombre=getattr(getattr(producto, "categoria", None), "nombre", None),
            precio=producto.precio,
            precio_oferta=producto.precio_oferta,
            precio_efectivo=producto.precio_efectivo(ahora),
            oferta_activa=producto.oferta_activa(ahora),
            estado=producto.estado,
            imagen_principal_url=(
                self.media_service.url_de(principal.imagen.name) if principal else None
            ),
            cantidad_imagenes=len(imagenes),
        )

    @staticmethod
    def result_categoria(categoria) -> CategoriaProductoResult:
        """Proyecta una categoría al result object."""
        return CategoriaProductoResult(
            id=categoria.id,
            nombre=categoria.nombre,
            slug=categoria.slug,
            orden=categoria.orden,
        )


__all__ = ["ProductoCoreService"]
