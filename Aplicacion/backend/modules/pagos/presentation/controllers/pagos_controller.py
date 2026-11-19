"""`PagosController` — superficie HTTP del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/PLAN_REFACTORIZACION.md` §1.A (controladores sagrados) ·
          `contract/django-app-architecture-contract.md` §4.8

Controller DELGADO: parsea la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter. Cero `if`, cero ORM, cero respuestas de
error manuales (los errores los construye el catálogo de `core/exceptions.py`
a partir del código estable de la excepción de dominio).

Rutas (ledger FR-07 §3.3):

| Ruta | Método | Scope | Permiso | Errores |
|---|---|---|---|---|
| `/pagos/ordenes/{orden_id}/confirmar` | POST | implícito | `TITULARIDAD_COMPRADOR` | `PAGO_FIRMA_INVALIDA` 400 · `PAGO_DATOS_INCONSISTENTES` 409 · `MONTO_NO_COINCIDE` 409 · `ORDEN_YA_PAGADA_CON_IZIPAY` 409 |
| `/pagos/izipay/notificacion` | POST | — | servidor a servidor (firma) | `PAGO_FIRMA_INVALIDA` 400 · `PAGO_NOTIFICACION_NO_VERIFICABLE` 400 |
| `/pagos/ordenes/{orden_id}` | GET | implícito | `TITULARIDAD_COMPRADOR` | `ORDEN_PAGO_NO_ENCONTRADA` 404 |

NOTA DE REGISTRO: una ruta no existe hasta que su controller está registrado
en `config/api.py` (FR-07 §3.1 regla 2). El registro lo hace A0; este paquete
lo deja listo y lo pide explícitamente (evidence FND-04, petición A0-03).
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import (
    PagosOrchestrator,
)
from modules.pagos.presentation.parsers import (
    construir_payload_proveedor,
    extraer_notificacion,
)
from modules.pagos.presentation.presenters.pago_presenter import (
    OrdenPagoPresenter,
    PagoNotificacionPresenter,
    PagosPresenter,
)
from modules.pagos.presentation.schemas.pago_schemas import (
    ConfirmarPagoIn,
    OrdenPagoOut,
    PagoConfirmadoOut,
)


@api_controller("/pagos", tags=["Pagos"])
class PagosController:
    """Superficie HTTP de los pagos."""

    @inject
    def __init__(self, orchestrator: PagosOrchestrator):
        self.orchestrator = orchestrator

    @route.post(
        "/ordenes/{orden_id}/confirmar",
        response={200: ApiResponse[PagoConfirmadoOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Confirma el pago de una orden.",
    )
    async def confirmar_pago(self, request, orden_id: str, payload: ConfirmarPagoIn):
        """Confirma el pago de una orden.

        Route: POST /api/pagos/ordenes/{orden_id}/confirmar
        Auth: requiere sesión y titularidad de la orden.

        La idempotencia viaja en el header `Idempotency-Key` (FR-04 §2.2):
        la misma clave con el mismo cuerpo devuelve el MISMO resultado; con
        otro cuerpo devuelve 409.

        El navegador NO es fuente de confianza: la firma del proveedor se
        verifica en servidor antes de mutar nada (FR-04 §3).
        """
        payload_proveedor = construir_payload_proveedor(
            payload_http=payload.payload_http,
            transaction_id=payload.transaction_id,
            code=payload.code,
            message=payload.message,
            order_number=payload.order_number,
            amount=payload.amount,
            currency=payload.currency,
            signature=payload.signature,
            respuesta=payload.response,
        )
        result = await self.orchestrator.confirmar_pago(
            orden_pago_id=orden_id,
            payload=payload_proveedor,
            persona_id=_persona_id(request),
            ambito_idempotencia=f"pagos:confirmar:{orden_id}",
            clave_idempotencia=request.headers.get("Idempotency-Key"),
        )
        return success_response(
            PagosPresenter.present_confirmado(result),
            message="Pago confirmado correctamente.",
        )

    @route.post(
        "/izipay/notificacion",
        response={200: ApiResponse[PagoConfirmadoOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Notificación de pago del proveedor.",
    )
    async def notificacion_pago(self, request):
        """Notificación de pago del proveedor (servidor a servidor).

        Route: POST /api/pagos/izipay/notificacion
        Auth: pública por necesidad del proveedor — la autoridad viene de la
        FIRMA del comercio, no de una sesión.

        No hay fallback: sin clave del comercio y sin firma válida la
        notificación se rechaza y no se muta ninguna fila (FR-04 §3).

        La notificación es idempotente: una repetición o una llegada tardía
        converge al mismo resultado y no duplica derechos (FR-04 I-1).
        """
        payload_http, signature = extraer_notificacion(request)
        result = await self.orchestrator.confirmar_notificacion(
            payload_http=payload_http,
            signature=signature,
        )
        return success_response(
            PagoNotificacionPresenter.present_confirmado(result),
            message="Pago confirmado correctamente.",
        )

    @route.get(
        "/ordenes/{orden_id}",
        response={200: ApiResponse[OrdenPagoOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Estado de una orden de pago.",
    )
    async def obtener_orden(self, request, orden_id: str):
        """Estado de una orden de pago.

        Route: GET /api/pagos/ordenes/{orden_id}
        Auth: requiere sesión y titularidad de la orden.

        Devuelve el veredicto operativo (`estado_operativo`) y el historial de
        intentos. El cliente NUNCA cruza por su cuenta los estados hermanos:
        el veredicto lo calcula el backend (FR-01 §5, `RN-C07`).
        """
        result = await self.orchestrator.obtener_orden(
            orden_pago_id=orden_id,
            persona_id=_persona_id(request),
        )
        return success_response(OrdenPagoPresenter.present_orden(result))


def _persona_id(request) -> str | None:
    """La persona del actor autenticado, si la tiene.

    Una cuenta técnica puede no tener persona: entonces no hay comprador y la
    operación se rechaza con `PAGO_NO_AUTORIZADO` (el flujo lo decide).
    """
    actor = getattr(request, "auth", None)
    persona_id = getattr(actor, "persona_fk_id", None)
    return str(persona_id) if persona_id else None


__all__ = ["PagosController"]
