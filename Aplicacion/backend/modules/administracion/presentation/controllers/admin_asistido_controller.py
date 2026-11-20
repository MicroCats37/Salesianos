"""`AdminAsistidoController` — los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

| Ruta | Método | Wrapper |
|---|---|---|
| `/administracion/equipos/{equipo_id}/participantes` | POST | `ParticipanteAsistidoOut` |
| `/administracion/pases/compras-cliente` | POST | `CompraAsistidaOut` |
| `/administracion/marketplace/pedidos-cliente` | POST | `CompraAsistidaOut` |

**401 ANTES QUE 403**: las rutas declaran `auth=JWTAuth()` y una capacidad de
escritura. Un anónimo recibe 401 antes de que la capacidad se compruebe
(`core/permissions.py`).

El controller es "SAGRADO": cero lógica (`contract/PLAN_REFACTORIZACION.md`
§1.A). Sólo parsea, delega al orquestador y devuelve el éxito formateado por
el presenter. Los errores los traduce el catálogo global de
`core/exceptions.py`.

## La REGLA que este surface respeta

**El COMPRADOR es el CLIENTE, no el administrador.** Estas rutas compran PARA
un tercero: la identidad del cliente viaja en el cuerpo y el administrador es
el ACTOR de la operación (queda en el acta). Ninguna de estas rutas relaja la
propiedad de las rutas públicas: el comprador público sigue siendo la cuenta
autenticada o la identidad civil declarada en su checkout.

**La CAPACIDAD de las compras asistidas es la MISMA de la aprobación manual
canónica** (`RequireAdminVer`, la de `POST /administracion/pagos/{orden}/
aprobar-manual`): estas rutas liquidan el pago con el mismo flujo del dueño.
El alta de participante, en cambio, exige además `admin.equipos.escribir`,
porque escribe en el dominio de los equipos.
"""

from uuid import UUID

from injector import inject
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.permissions import RequireAdminVer, RequireEquiposEscribir
from core.responses import ApiResponse, success_response
from modules.administracion.domain.schemas.admin_asistido_schemas import (
    AsignarParticipanteEquipoData,
    ClienteAsistidoData,
    ComprarPaseParaClienteData,
    ComprarPedidoParaClienteData,
    EvidenciaPagoAsistidoData,
    ItemPedidoAsistidoData,
)
from modules.administracion.domain.services.orchestrators.admin_asistido_orchestrator import (
    AdminAsistidoOrchestrator,
)
from modules.administracion.presentation.presenters.admin_asistido_presenter import (
    AdminAsistidoPresenter,
)
from modules.administracion.presentation.schemas.admin_asistido_schemas import (
    AgregarParticipanteEquipoIn,
    ComprarPaseClienteIn,
    ComprarPedidoClienteIn,
    CompraAsistidaOut,
    ParticipanteAsistidoOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminAsistidoController:
    """Los comandos administrativos asistidos."""

    @inject
    def __init__(self, orchestrator: AdminAsistidoOrchestrator):
        self.orchestrator = orchestrator

    # ── Participantes ───────────────────────────────────────────────────────

    @route.post(
        "/equipos/{equipo_id}/participantes",
        response={201: ApiResponse[ParticipanteAsistidoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer, RequireEquiposEscribir],
        summary="Agrega una persona existente a la plantilla de un equipo.",
    )
    async def agregar_participante(
        self,
        request,
        equipo_id: UUID,
        payload: AgregarParticipanteEquipoIn,
    ):
        """Route: POST /api/administracion/equipos/{equipo_id}/participantes

        Agrega a la plantilla del equipo una persona que YA está en el padrón,
        identificada por su tipo y número de documento exactos.

        El comando NO crea una persona y NO borra ninguna: sólo da de alta una
        `Participacion`. Las reglas de la plantilla (capacidad del equipo,
        duplicado, disciplina permitida, compatibilidad de género y saldo de
        cupos) las aplica el módulo DUEÑO y este comando no las reimplementa.

        El motivo es OBLIGATORIO (422 `MOTIVO_REQUERIDO`) y la acción queda
        en el ACTA transversal.
        """
        resultado = await self.orchestrator.agregar_participante(
            request.auth,
            AsignarParticipanteEquipoData(
                equipo_id=equipo_id,
                tipo_documento=payload.tipo_documento,
                numero_documento=payload.numero_documento,
                rol=payload.rol,
                motivo=payload.motivo,
            ),
        )

        return success_response(
            AdminAsistidoPresenter.present_participante(resultado),
            message="El participante se agregó al equipo correctamente.",
        )

    # ── Compras asistidas ───────────────────────────────────────────────────

    @route.post(
        "/pases/compras-cliente",
        response={201: ApiResponse[CompraAsistidaOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="Compra un lote de pases para un cliente y registra su pago.",
    )
    async def comprar_pase_para_cliente(
        self,
        request,
        payload: ComprarPaseClienteIn,
    ):
        """Route: POST /api/administracion/pases/compras-cliente

        Compra un lote de pases PARA un cliente identificado por su
        documento, con su nombre y su correo de contacto, y registra el pago
        externo con su evidencia.

        El COMPRADOR es el cliente: la compra y el lote quedan a su nombre y
        el administrador es el ACTOR de la operación, no el dueño de la
        compra. El precio lo congela el servidor contra el catálogo vigente
        y el pago lo liquida el módulo DUEÑO del pago.
        """
        resultado = await self.orchestrator.comprar_pase_para_cliente(
            request.auth,
            ComprarPaseParaClienteData(
                pase_id=payload.pase_id,
                cantidad=payload.cantidad,
                cliente=_cliente(payload.cliente),
                evidencia=_evidencia(payload.evidencia),
            ),
        )

        return success_response(
            AdminAsistidoPresenter.present_compra(resultado),
            message="La compra de pases para el cliente se registró correctamente.",
        )

    @route.post(
        "/marketplace/pedidos-cliente",
        response={201: ApiResponse[CompraAsistidaOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="Crea un pedido de tienda para un cliente y registra su pago.",
    )
    async def comprar_pedido_para_cliente(
        self,
        request,
        payload: ComprarPedidoClienteIn,
    ):
        """Route: POST /api/administracion/marketplace/pedidos-cliente

        Crea un pedido de tienda PARA un cliente identificado por su
        documento, con su nombre y su correo de contacto, y registra el pago
        externo con su evidencia.

        El COMPRADOR es el cliente: el pedido y su compra quedan a su nombre y
        el administrador es el ACTOR de la operación. Los precios los congela
        el servidor contra el catálogo vigente y el stock se reserva en la
        misma transacción del alta.
        """
        resultado = await self.orchestrator.comprar_pedido_para_cliente(
            request.auth,
            ComprarPedidoParaClienteData(
                items=[
                    ItemPedidoAsistidoData(
                        tipo=item.tipo,
                        producto_id=item.producto_id,
                        cantidad=item.cantidad,
                    )
                    for item in payload.items
                ],
                cliente=_cliente(payload.cliente),
                evidencia=_evidencia(payload.evidencia),
            ),
        )

        return success_response(
            AdminAsistidoPresenter.present_compra(resultado),
            message="El pedido para el cliente se registró correctamente.",
        )


def _cliente(payload) -> ClienteAsistidoData:
    """El DTO interno del cliente, desde su schema HTTP."""
    return ClienteAsistidoData(
        tipo_documento=payload.tipo_documento,
        numero_documento=payload.numero_documento,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        contacto_email=payload.contacto_email,
    )


def _evidencia(payload) -> EvidenciaPagoAsistidoData:
    """El DTO interno de la evidencia, desde su schema HTTP."""
    return EvidenciaPagoAsistidoData(
        canal=payload.canal,
        referencia=payload.referencia,
        motivo=payload.motivo,
    )


__all__ = ["AdminAsistidoController"]
