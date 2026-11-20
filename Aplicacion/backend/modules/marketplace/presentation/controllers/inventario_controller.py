"""`InventarioController` — superficie HTTP del inventario y de las entregas.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/routes/SH-05-provisional-endpoint-and-presenter-register.md`
Contract: `contract/django-app-architecture-contract.md` §4.8 ·
          `contract/api-wrapper-presenter-contract.md` §2, §8

Controller DELGADO: hidrata la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter. Cero `if` de negocio, cero ORM, cero
respuestas de error manuales (los errores los construye el catálogo de
`core/exceptions.py` a partir del código estable de la excepción).

Rutas (**PROVISIONALES** · SH-05 §1.6 · RB-07):

| Ruta | Método | Permiso | Errores |
|---|---|---|---|
| `/administracion/marketplace/inventario` | GET | `Administrador` | `MODULO_NO_HABILITADO` 409 |
| `/administracion/marketplace/inventario/movimientos` | POST | `Administrador` | `PRODUCTO_NO_ENCONTRADO` 404 · `STOCK_INSUFICIENTE` 409 · `MOVIMIENTO_INVENTARIO_INVALIDO` 422 |
| `/administracion/marketplace/inventario/movimientos/{id}/revertir` | POST | `Administrador` | `MOVIMIENTO_INVENTARIO_NO_ENCONTRADO` 404 · `STOCK_INSUFICIENTE` 409 |
| `/administracion/marketplace/entregas` | GET | `Administrador` | `MODULO_NO_HABILITADO` 409 |
| `/administracion/marketplace/entregas/{pedido_id}/confirmar` | POST | `Administrador` | `PEDIDO_NO_ENCONTRADO` 404 · `PEDIDO_NO_PAGADO` 409 · `PEDIDO_NO_ENTREGABLE` 409 |

**UNA SALIDA SIN VENTA NO ES UNA COMPRA (RN-M05 · `QA-M02`).** La ruta de
movimientos NO crea compra, ni orden de pago, ni pedido: el movimiento es el
único hecho que deja la operación.

**PAGADO NO ES ENTREGADO (RN-M07).** Confirmar la entrega exige un pedido
PAGADO y mueve SÓLO el estado de la entrega: ni el pago ni el pedido cambian.

**NOTA DE REGISTRO (FR-07 §3.1 regla 2):** una ruta no existe hasta que su
controller está registrado en `config/api.py`. Este paquete NO edita
`config/api.py` (es de A0): el registro de estas rutas PROVISIONALES se
pide como evidencia (petición A0-01 del evidence de DOM-06).
"""

from uuid import UUID

from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response

from modules.marketplace.domain.schemas.inventario_schemas import (
    RegistrarMovimientoInventarioData,
    RevertirMovimientoInventarioData,
)
from modules.marketplace.domain.services.orchestrators.inventario_orchestrator import (
    InventarioOrchestrator,
)
from modules.marketplace.domain.services.orchestrators.pedido_orchestrator import (
    PedidoOrchestrator,
)
from modules.marketplace.presentation.presenters.inventario_presenter import (
    EntregaPresenter,
    InventarioPresenter,
)
from modules.marketplace.presentation.schemas.inventario_schemas import (
    EntregaConfirmadaOut,
    EntregasOut,
    InventarioProductoOut,
    MovimientoInventarioOut,
    RegistrarMovimientoInventarioIn,
    RevertirMovimientoInventarioIn,
)


@api_controller("/administracion/marketplace", tags=["Marketplace"])
class InventarioController:
    """Superficie HTTP del inventario y de las entregas de la tienda."""

    @inject
    def __init__(
        self,
        orchestrator: InventarioOrchestrator,
        pedido_orchestrator: PedidoOrchestrator,
    ):
        self.orchestrator = orchestrator
        self.pedido_orchestrator = pedido_orchestrator

    # ── RT-MK-08 · GET /administracion/marketplace/inventario ────────────────

    @route.get(
        "/inventario",
        response={200: ApiResponse[list[InventarioProductoOut]]},
        summary="Inventario de la edición vigente con su bitácora",
        permissions=[RequireAdmin],
    )
    async def listar_inventario(self):
        """El inventario de la edición vigente.

        Route: GET /api/administracion/marketplace/inventario

        Cada producto expone el stock FÍSICO, lo RESERVADO por pedidos
        pendientes y lo DISPONIBLE: los tres son hechos distintos y el
        cliente no calcula ninguno (`RN-M06`).
        """
        items = await self.orchestrator.listar_inventario()
        return success_response(InventarioPresenter.present_inventario_lista(items))

    # ── RT-MK-09 · POST /administracion/marketplace/inventario/movimientos ──

    @route.post(
        "/inventario/movimientos",
        response={201: ApiResponse[MovimientoInventarioOut]},
        summary="Registro de una entrada, salida o ajuste de inventario",
        permissions=[RequireAdmin],
    )
    async def registrar_movimiento(self, request, payload: RegistrarMovimientoInventarioIn):
        """Registra un movimiento de inventario.

        Route: POST /api/administracion/marketplace/inventario/movimientos

        El movimiento declara el producto, la cantidad CON SIGNO, el motivo y
        el actor (el de la sesión). **No crea compra ni pago** (`RN-M05`).
        """
        data = RegistrarMovimientoInventarioData(
            producto_id=str(payload.producto_id),
            tipo=payload.tipo,
            cantidad=payload.cantidad,
            motivo=payload.motivo,
        )
        result = await self.orchestrator.registrar_movimiento(request.auth, data)
        return success_response(
            InventarioPresenter.present_movimiento(result),
            message="El movimiento de inventario se registró correctamente.",
        )

    # ── RT-MK-12 · POST …/inventario/movimientos/{id}/revertir ──────────────

    @route.post(
        "/inventario/movimientos/{movimiento_id}/revertir",
        response={201: ApiResponse[MovimientoInventarioOut]},
        summary="Compensa un movimiento de inventario ya registrado",
        permissions=[RequireAdmin],
    )
    async def revertir_movimiento(
        self,
        request,
        movimiento_id: UUID,
        payload: RevertirMovimientoInventarioIn,
    ):
        """Compensa un movimiento con otro de signo contrario.

        Route: POST /api/administracion/marketplace/inventario/movimientos/{id}/revertir

        El movimiento original NO se edita ni se borra: queda la traza y
        aparece la reversa (`RN-M04`).
        """
        data = RevertirMovimientoInventarioData(
            movimiento_id=str(movimiento_id),
            motivo=payload.motivo,
        )
        result = await self.orchestrator.revertir_movimiento(request.auth, data)
        return success_response(
            InventarioPresenter.present_movimiento(result),
            message="La reversa del movimiento se registró correctamente.",
        )

    # ── RT-MK-10 · GET /administracion/marketplace/entregas ─────────────────

    @route.get(
        "/entregas",
        response={200: ApiResponse[EntregasOut]},
        summary="Recogidas pendientes y entregadas de la edición vigente",
        permissions=[RequireAdmin],
    )
    async def listar_entregas(self):
        """Las colas de recogidas pendientes y entregadas.

        Route: GET /api/administracion/marketplace/entregas

        Ambas tablas se deciden por el estado de la ENTREGA (`RN-M07` ·
        `QA-M04`), no por el pago.
        """
        items = await self.orchestrator.listar_entregas()
        return success_response(EntregaPresenter.present_listado(items))

    # ── RT-MK-11 · POST …/entregas/{pedido_id}/confirmar ────────────────────

    @route.post(
        "/entregas/{pedido_id}/confirmar",
        response={201: ApiResponse[EntregaConfirmadaOut]},
        summary="Confirma la entrega de un pedido pagado",
        permissions=[RequireAdmin],
    )
    async def confirmar_entrega(self, request, pedido_id: UUID):
        """Confirma la entrega de un pedido.

        Route: POST /api/administracion/marketplace/entregas/{pedido_id}/confirmar

        Es **IDEMPOTENTE**: un reintento del operador devuelve el MISMO
        acta, no la duplica.
        """
        result = await self.pedido_orchestrator.confirmar_entrega(
            request.auth,
            str(pedido_id),
        )
        return success_response(
            EntregaPresenter.present_confirmada(result),
            message="La entrega se registró correctamente.",
        )


__all__ = ["InventarioController"]
