"""`AdminPagoController` — la superficie HTTP de los pagos.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

| Ruta | Método | Ledger | Wrapper |
|---|---|---|---|
| `/administracion/pagos` | GET | `RT-PG-04` | `PaginatedData[AdminPagoListItemOut]` |
| `/administracion/pagos/{compra_id}` | GET | `RT-PG-07` | `AdminPagoDetalleOut` |

## La ruta que NO existe: `RT-PG-05` (aprobación manual)

`RT-PG-05` (`POST /administracion/pagos/{orden_pago_id}/aprobar-manual`) está
CONGELADA en `GOV-01` pero **este paquete NO la implementa**, y el motivo es
de ARQUITECTURA, no de tiempo:

- La aprobación manual es un HECHO COMERCIAL: deja una evidencia, liquida la
  compra y habilita los derechos.
- El objetivo **no tiene** un modelo de aprobación manual persistido ni un
  servicio que la aplique: `pagos` y `commerce` no publican esa operación.
- Implementarla aquí sería crear en el módulo de agregación la propiedad de
  un dataset que es de otro dueño (`no duplicated dataset ownership`) y
  decidir sus reglas de liquidación (`admin aggregates do not own domain
  rules`).

Por tanto la ruta **NO EXISTE** y su ledger sigue en `registrado: false` con
este motivo. La petición al dueño está en `A0-XCT02-10`.

**401 ANTES QUE 403**: `auth=JWTAuth()` + la capacidad `admin.ver`.
"""

from datetime import datetime
from typing import Optional

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.exceptions import NotFoundError
from core.pagination import PaginatedData
from core.permissions import RequireAdminVer
from core.responses import ApiResponse, paginated_response, success_response
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_operacion_presenter import (
    AdminOperacionPresenter,
)
from modules.administracion.presentation.schemas.admin_operacion_schemas import (
    AprobarPagoManualIn,
    AdminPagoDetalleOut,
    AdminPagoListItemOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminPagoController:
    """Los pagos del panel de administración."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/pagos",
        response={200: ApiResponse[PaginatedData[AdminPagoListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="La lista operativa de los pagos.",
    )
    async def listar_pagos(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None, description="Edición del listado. Sin valor, la edición publicada."
        ),
        q: Optional[str] = Query(None, description="Búsqueda sobre la referencia o el comprador."),
        ordering: Optional[str] = Query(
            None, description="Orden (lista blanca): created_at, estado, monto."
        ),
        estado_operativo: Optional[str] = Query(
            None, description="Filtro del veredicto operativo del pago."
        ),
        estado_compra: Optional[str] = Query(None, description="Filtro del estado de la compra."),
        estado_orden: Optional[str] = Query(None, description="Filtro del estado de la orden."),
        tipo: Optional[str] = Query(None, description="Filtro del origen de la compra."),
        desde: Optional[datetime] = Query(None, description="Comienzo del rango de fechas."),
        hasta: Optional[datetime] = Query(None, description="Fin del rango de fechas."),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/pagos

        `RT-PG-04`. El VEREDICTO de cada fila lo calcula el dueño
        (`EstadoOperativoPagoService`): el filtro `estado_operativo` se
        aplica sobre ese veredicto, que es la misma fuente y la misma regla.
        """
        items, total, pagina, tamano, paginas = (
            await self.orchestrator.listar_pagos(
                edicion_id=edicion_id,
                q=q or "",
                ordering=ordering or "",
                estado_operativo=estado_operativo or "",
                estado_compra=estado_compra or "",
                estado_orden=estado_orden or "",
                tipo=tipo or "",
                desde=desde,
                hasta=hasta,
                page=page,
                page_size=page_size,
            )
        )

        return paginated_response(
            items=[AdminOperacionPresenter.present_pago_lista(item) for item in items],
            total=total,
            page=pagina,
            page_size=tamano,
        )

    @route.get(
        "/pagos/{compra_id}",
        response={200: ApiResponse[AdminPagoDetalleOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El detalle comercial de un pago.",
    )
    async def obtener_pago(self, request, compra_id: str):
        """Route: GET /api/administracion/pagos/{compra_id}

        `RT-PG-07`. El detalle publica la compra, la procedencia de la
        evidencia y los intentos del proveedor. **No** publica
        `referencia_proveedor`, `evidencia`, `metadata` ni
        `mensaje_respuesta`: son datos técnicos del proveedor
        (`FR-04` §1.3).
        """
        detalle = await self.orchestrator.obtener_pago(compra_id)

        if detalle is None:
            raise NotFoundError(resource="Pago", code="RESOURCE_NOT_FOUND")

        return success_response(AdminOperacionPresenter.present_pago_detalle(detalle))

    @route.post(
        "/pagos/{orden_pago_id}/aprobar-manual",
        response={200: ApiResponse[AdminPagoListItemOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="Registra evidencia de un pago externo.",
    )
    async def aprobar_pago_manual(
        self, request, orden_pago_id: str, payload: AprobarPagoManualIn
    ):
        """Confirma una orden sin crear ni fingir una transacción de proveedor."""
        item = await self.orchestrator.aprobar_pago_manual(
            orden_pago_id=orden_pago_id,
            actor_id=str(request.auth.id),
            canal=payload.canal,
            referencia=payload.referencia,
            motivo=payload.motivo,
        )
        if item is None:
            raise NotFoundError(resource="Pago", code="RESOURCE_NOT_FOUND")
        return success_response(AdminOperacionPresenter.present_pago_lista(item))


__all__ = ["AdminPagoController"]
