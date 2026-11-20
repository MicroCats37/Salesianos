"""`AdminAsistidoOrchestrator` — la fachada async de los comandos asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/django-app-architecture-contract.md` §4.5 — el
orquestador es una fachada async EXTREMADAMENTE delgada: un método público
por endpoint y SÓLO delegación.

No contiene lógica de negocio: el motivo, la identidad del cliente, la
aprobación del pago y el acta son del flujo (`AdminAsistidoFlujo`), y los
efectos son de los módulos DUEÑOS.
"""

from injector import inject

from modules.administracion.domain.schemas.admin_asistido_schemas import (
    AsignarParticipanteEquipoData,
    ComprarPaseParaClienteData,
    ComprarPedidoParaClienteData,
)
from modules.administracion.domain.services.flujos.admin_asistido_flujo import (
    AdminAsistidoFlujo,
)


class AdminAsistidoOrchestrator:
    """La fachada async de los comandos administrativos asistidos."""

    @inject
    def __init__(self, flujo: AdminAsistidoFlujo):
        self.flujo = flujo

    async def agregar_participante(self, actor, data: AsignarParticipanteEquipoData):
        """Agrega una persona existente a la plantilla de un equipo."""
        return await self.flujo.agregar_participante(actor, data)

    async def comprar_pase_para_cliente(
        self,
        actor,
        data: ComprarPaseParaClienteData,
    ):
        """Compra un lote de pases para un cliente y registra su pago."""
        return await self.flujo.comprar_pase_para_cliente(actor, data)

    async def comprar_pedido_para_cliente(
        self,
        actor,
        data: ComprarPedidoParaClienteData,
    ):
        """Crea un pedido de tienda para un cliente y registra su pago."""
        return await self.flujo.comprar_pedido_para_cliente(actor, data)


__all__ = ["AdminAsistidoOrchestrator"]
