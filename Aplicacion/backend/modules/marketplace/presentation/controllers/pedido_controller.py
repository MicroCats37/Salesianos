"""`PedidoController` — superficie HTTP del pedido de marketplace.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
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
| `/marketplace/pedidos` | POST | implícito | autenticado | `PEDIDO_ITEMS_MIXTOS` 422 · `PEDIDO_ITEM_NO_PERMITIDO` 409 · `PEDIDO_CANTIDAD_INVALIDA` 422 · `PRODUCTO_NO_ENCONTRADO` 404 · `PRODUCTO_NO_DISPONIBLE` 409 · `MODULO_NO_HABILITADO` 409 · `COMPRADOR_SIN_PERSONA` 422 |
| `/marketplace/pedidos/{token}` | GET | implícito | público (el token es la credencial) | `PEDIDO_NO_ENCONTRADO` 404 · `PEDIDO_NO_AUTORIZADO` 403 |

**NO hay control de existencias.** La reserva de stock es de `DOM-06`
(`RN-M06`): este paquete NO inventa existencias ni las descuenta. El catálogo
no declara `stock` a propósito (DOM-04, `D-DOM04-06`).

**NOTA DE REGISTRO:** una ruta no existe hasta que su controller está
registrado en `config/api.py` (FR-07 §3.1 regla 2). Ese registro es de A0 y
este paquete NO edita `config/api.py`: lo pide como evidencia (petición
A0-01 del evidence de DOM-05).
"""

from asgiref.sync import sync_to_async
from injector import inject
from ninja_extra import api_controller, route

from core.responses import ApiResponse, success_response
from modules.marketplace.domain.schemas.pedido_schemas import PedidoCreateData
from modules.marketplace.domain.services.orchestrators.pedido_orchestrator import (
    PedidoOrchestrator,
)
from modules.marketplace.presentation.presenters.pedido_presenter import (
    PedidoPresenter,
    PedidoSeguimientoPresenter,
)
from modules.marketplace.presentation.schemas.pedido_schemas import (
    CrearPedidoIn,
    PedidoCreadoOut,
    PedidoSeguimientoOut,
)


@api_controller("/marketplace", tags=["Marketplace"])
class PedidoController:
    """Superficie HTTP del pedido de la tienda."""

    @inject
    def __init__(self, orchestrator: PedidoOrchestrator):
        self.orchestrator = orchestrator

    # ── RT-CM-03 · POST /marketplace/pedidos ───────────────────────────────

    @route.post(
        "/pedidos",
        response={201: ApiResponse[PedidoCreadoOut]},
        summary="Alta del pedido de marketplace con su snapshot de precio",
    )
    async def crear_pedido(self, request, payload: CrearPedidoIn):
        """Crea el pedido de una intención de compra.

        Route: POST /api/marketplace/pedidos

        El payload **no admite un importe**: el precio lo resuelve y congela
        el servidor contra el catálogo vigente (RN-C02). El alcance (edición)
        tampoco lo declara el cliente (RN-E01).

        Un reintento NO duplica el pedido: la identidad de la intención es la
        huella de los artículos, y el pedido existente se RECUPERA con su
        snapshot congelado (RN-C03, RN-C04).
        """
        data = PedidoCreateData(
            items=[
                {
                    "tipo": item.tipo,
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                }
                for item in payload.items
            ],
        )
        result = await self.orchestrator.crear_pedido(request.auth, data)
        return success_response(
            PedidoPresenter.present(result),
            message="El pedido se registró correctamente.",
        )

    # ── RT-MK-04 · GET /marketplace/pedidos/{token} ────────────────────────

    @route.get(
        "/pedidos/{token}",
        response={200: ApiResponse[PedidoSeguimientoOut]},
        summary="Seguimiento del pedido por su enlace privado",
        auth=None,
    )
    async def obtener_pedido(self, request, token: str):
        """El pedido de un enlace privado, con sus TRES estados.

        Route: GET /api/marketplace/pedidos/{token}

        El token es la credencial del enlace (P-01): un invitado sin sesión
        abre su pedido con él. Un actor AUTENTICADO que no es el comprador NO
        puede consultarlo, aunque conozca el token (RN-U02, FR-03 §2.1).

        `estado` (pedido), `estado_pago` (pago) y `estado_entrega` (entrega)
        son hechos DISTINTOS: un pedido pagado sigue con la entrega
        `PENDIENTE` (RN-M07, `QA-M04`).
        """
        actor = await _actor_opcional(request)
        result = await self.orchestrator.obtener_pedido_por_token(token, actor)
        return success_response(PedidoSeguimientoPresenter.present(result))


async def _actor_opcional(request):
    """El actor de la petición, o `None` si la petición es anónima.

    La ruta del enlace privado es PÚBLICA (el token es la credencial), pero
    hay que distinguir "invitado" de "autenticado que NO es el comprador": el
    primero puede abrir el pedido con el token; el segundo recibe 403
    (RN-U02). La credencial se resuelve SÓLO si viene.

    Una credencial presente pero rota responde 401 con el catálogo global:
    el módulo no decide el status de la autenticación.
    """
    from ninja_jwt.authentication import JWTAuth

    cabecera = request.headers.get("Authorization") or ""
    partes = cabecera.split(" ")
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return None
    return await sync_to_async(JWTAuth().authenticate)(request, partes[1])


__all__ = ["PedidoController"]
