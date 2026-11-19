"""`ProductoController` — superficie HTTP del módulo `marketplace`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/django-app-architecture-contract.md` §4.8 ·
          `contract/api-wrapper-presenter-contract.md` §2, §8

Controller DELGADO: hidrata la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter. Cero `if` de negocio, cero ORM, cero
respuestas de error manuales (los errores los construye el catálogo de
`core/exceptions.py` a partir del código estable de la excepción).

Rutas (ledger FR-07 §3.3):

| Ruta | Método | Scope | Permiso | Errores |
|---|---|---|---|---|
| `/marketplace/productos` | POST | implícito | `Administrador` | `MEDIA_TIPO_NO_PERMITIDO` 400 · `MEDIA_ARCHIVO_HUERFANO` 400 · `MEDIA_TOKEN_NO_RESUELTO` 400 · `MEDIA_TOKEN_DUPLICADO` 400 · `MEDIA_TAMANO_EXCEDIDO` 413 |
| `/marketplace/categorias` | GET | implícito | público | `EDICION_NO_PUBLICADA` 404 · `EDICION_AMBIGUA` 409 |
| `/marketplace/productos` | GET | implícito | público | idem |
| `/marketplace/productos/{slug}` | GET | implícito | público | idem + `PRODUCTO_NO_ENCONTRADO` 404 |

NOTA DE REGISTRO: una ruta no existe hasta que su controller está registrado
en `config/api.py` (FR-07 §3.1 regla 2). Ese registro es de A0 y este paquete
NO edita `config/api.py`: lo pide como evidencia (petición A0-03).
"""

from injector import inject
from ninja_extra import api_controller, route

from core.pagination import PaginatedData
from core.permissions import RequireAdmin
from core.responses import ApiResponse, paginated_response, success_response
from modules.marketplace.domain.services.orchestrators.producto_orchestrator import (
    ProductoOrchestrator,
)
from modules.marketplace.presentation.hydration.producto_hydrator import ProductoHydrator
from modules.marketplace.presentation.presenters.producto_presenter import (
    CategoriaListaPresenter,
    ProductoDetallePresenter,
    ProductoListaPresenter,
    ProductoPresenter,
)
from modules.marketplace.presentation.schemas.producto_schemas import (
    CategoriaListaOut,
    CrearProductoIn,
    ProductoDetalleOut,
    ProductoListItemOut,
    ProductoOut,
)


@api_controller("/marketplace", tags=["Marketplace"])
class ProductoController:
    """Superficie HTTP del catálogo de la tienda."""

    @inject
    def __init__(self, orchestrator: ProductoOrchestrator):
        self.orchestrator = orchestrator

    # ── RT-MD-01 · POST /marketplace/productos ─────────────────────────────

    @route.post(
        "/productos",
        response={200: ApiResponse[ProductoOut]},
        summary="Alta de un producto con su galería ordenada",
        permissions=[RequireAdmin],
    )
    async def crear_producto(self, request):
        """Alta de un producto.

        Route: POST /api/marketplace/productos

        Acepta el protocolo multipart congelado (FR-06 §2.4): el campo `data`
        con el JSON del payload y el campo `files` con las partes
        `<token>___<realname>`. También acepta JSON para el alta SIN
        imágenes.

        El alcance (edición) lo resuelve el servidor; el cliente no lo
        elige.
        """
        data = ProductoHydrator.hydrate(request)
        result = await self.orchestrator.crear_producto(data)
        return success_response(ProductoPresenter.present(result))

    # ── RT-MK-01 · GET /marketplace/categorias ─────────────────────────────

    @route.get(
        "/categorias",
        response={200: ApiResponse[list[CategoriaListaOut]]},
        summary="Categorías del catálogo de la edición vigente",
        auth=None,
    )
    async def listar_categorias(self):
        """Categorías del catálogo.

        Route: GET /api/marketplace/categorias
        """
        items = await self.orchestrator.listar_categorias()
        return success_response(CategoriaListaPresenter.present_categorias(items))

    # ── RT-MK-02 · GET /marketplace/productos ─────────────────────────────

    @route.get(
        "/productos",
        response={200: ApiResponse[PaginatedData[ProductoListItemOut]]},
        summary="Catálogo de productos de la edición vigente",
        auth=None,
    )
    async def listar_productos(self, categoria_id=None, page: int = 1, page_size: int = 25):
        """Catálogo de productos.

        Route: GET /api/marketplace/productos

        La paginación usa la forma ÚNICA del contrato: el total y los
        metadatos viven DENTRO de `data`.
        """
        items, total = await self.orchestrator.listar_productos(
            categoria_id=categoria_id, page=page, page_size=page_size
        )
        return paginated_response(
            ProductoListaPresenter.present_lista(items),
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── RT-MK-03 · GET /marketplace/productos/{slug} ───────────────────────

    @route.get(
        "/productos/{slug}",
        response={200: ApiResponse[ProductoDetalleOut]},
        summary="Detalle de un producto con su galería ordenada",
        auth=None,
    )
    async def obtener_producto(self, slug: str):
        """Detalle de un producto.

        Route: GET /api/marketplace/productos/{slug}

        La galería viaja ORDENADA (`orden ASC, id ASC`) y cada imagen expone
        si su archivo sigue disponible en el volumen (FR-06 §2.7).
        """
        result = await self.orchestrator.obtener_producto(slug)
        return success_response(ProductoDetallePresenter.present_detalle(result))


__all__ = ["ProductoController"]
