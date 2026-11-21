"""`ValidacionController` — la superficie HTTP de la consola de validación.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0`

Ledger: `RT-RT-01` (POST `/validaciones/preview`) ·
        `RT-RT-02` (POST `/validaciones/confirmar`) ·
        `RT-RT-04` (POST `/validaciones/tickets`).

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.

**EL OPERADOR.** Las dos rutas exigen una cuenta autenticada con la
capacidad `admin.acreditaciones.escribir`: el grupo autoriza a OPERAR el
punto de control, y el DERECHO autoriza a ingresar o canjear
(`contratos/02` §6). Un ticket NO es un permiso.

**401 ANTES QUE 403**: un anónimo recibe 401 antes de que la capacidad se
compruebe (`core/permissions.py`).

**LA CREDENCIAL NO SE DEVUELVE.** Ni el preview ni la confirmación incluyen
el código que el operador escaneó: es un secreto (`RN-P06`).
"""

from injector import inject
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.permissions import RequireAcreditacionesEscribir
from core.responses import ApiResponse, success_response
from modules.validaciones.domain.schemas.validacion_schemas import (
    ConfirmarTicketData,
    EmitirTicketData,
    PreviewTicketData,
)
from modules.validaciones.domain.services.orchestrators.validacion_orchestrator import (
    ValidacionOrchestrator,
)
from modules.validaciones.presentation.presenters.ticket_presenter import (
    TicketConfirmPresenter,
    TicketEmitidoPresenter,
    TicketPreviewPresenter,
)
from modules.validaciones.presentation.schemas.validacion_schemas import (
    ConfirmarTicketIn,
    EmitirTicketIn,
    PreviewTicketIn,
    TicketConfirmadoOut,
    TicketEmitidoOut,
    TicketPreviewOut,
)


@api_controller("/validaciones", tags=["Validaciones"])
class ValidacionController:
    """La comprobación y el canje de credenciales de control de acceso."""

    @inject
    def __init__(self, orchestrator: ValidacionOrchestrator):
        self.orchestrator = orchestrator

    # ── RT-RT-01 · Vista previa ───────────────────────────────────────────────

    @route.post(
        "/preview",
        response={200: ApiResponse[TicketPreviewOut]},
        auth=JWTAuth(),
        permissions=[RequireAcreditacionesEscribir],
        summary="Comprueba una credencial sin consumirla.",
    )
    async def preview(self, request, payload: PreviewTicketIn):
        """Route: POST /api/validaciones/preview

        `RT-RT-01`. Es una LECTURA: no muta, no consume y no escribe
        (`RN-P06`). El veredicto lo publica el módulo DUEÑO del derecho.
        """
        data = PreviewTicketData(codigo=payload.codigo)
        result = await self.orchestrator.preview(data)
        return success_response(
            TicketPreviewPresenter.present(result),
            message="Credencial comprobada correctamente.",
        )

    # ── RT-RT-02 · Confirmación ───────────────────────────────────────────────

    @route.post(
        "/confirmar",
        response={201: ApiResponse[TicketConfirmadoOut]},
        auth=JWTAuth(),
        permissions=[RequireAcreditacionesEscribir],
        summary="Confirma el canje de una credencial.",
    )
    async def confirmar(self, request, payload: ConfirmarTicketIn):
        """Route: POST /api/validaciones/confirmar

        `RT-RT-02`. Revalida BAJO BLOQUEO y consume de forma ATÓMICA e
        IDEMPOTENTE (`FR-05` §2.2). Una repetición con la misma clave
        devuelve el MISMO resultado con `repetido = true`: no es un error.
        """
        data = ConfirmarTicketData(
            codigo=payload.codigo,
            idempotency_key=payload.idempotency_key,
            cantidad=payload.cantidad,
        )
        result = await self.orchestrator.confirmar(request.auth, data)
        return success_response(
            TicketConfirmPresenter.present(result),
            message="El canje se registró correctamente.",
        )

    # ── RT-RT-04 · Emisión de la credencial ──────────────────────────────────

    @route.post(
        "/tickets",
        response={201: ApiResponse[TicketEmitidoOut]},
        auth=JWTAuth(),
        permissions=[RequireAcreditacionesEscribir],
        summary="Emite la credencial de un derecho de entrada.",
    )
    async def emitir_ticket(self, request, payload: EmitirTicketIn):
        """Route: POST /api/validaciones/tickets

        Emite la credencial escaneable de un derecho de entrada. El cliente
        declara SÓLO el derecho: el tipo y la operación los deriva el módulo
        dueño (`RN-U04`), y el CÓDIGO lo genera el servidor.

        **EL CÓDIGO SE DEVUELVE UNA VEZ.** Es un secreto: no se publica en
        ningún listado, no se registra en la auditoría y no se escribe en
        ningún log. Esta respuesta es su única entrega.
        """
        data = EmitirTicketData(derecho_id=str(payload.derecho_id))
        result = await self.orchestrator.emitir_ticket(data)
        return success_response(
            TicketEmitidoPresenter.present(result),
            message="Credencial emitida correctamente.",
        )


__all__ = ["ValidacionController"]
