"""`PedidoOrchestrator` — fachada async del pedido de marketplace.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.5

Fachada MUY DELGADA: delega en el flujo y devuelve result objects, nunca
schemas HTTP. No contiene lógica de negocio.

Lo que SÍ hace (y es del presentador, no del controller) es resolver el
COMPRADOR: la persona de la cuenta autenticada. El documento de identidad no
es una credencial (RN-U04), así que el comprador sólo puede ser la cuenta
autenticada; una cuenta sin persona vinculada no puede comprar (el código
`COMPRADOR_SIN_PERSONA` es el congelado por DOM-01).
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.marketplace.domain.exceptions import CompradorSinPersonaError
from modules.marketplace.domain.ports.titularidad import ITitularidadActorService
from modules.marketplace.domain.results.pedido_result import (
    PedidoCreadoResult,
    PedidoSeguimientoResult,
)
from modules.marketplace.domain.schemas.pedido_schemas import PedidoCreateData
from modules.marketplace.domain.services.flujos.pedido_flujo import PedidoFlujo
from modules.salesianos_fest.domain.ports import IObtensionPersonaService


class PedidoOrchestrator:
    """Fachada async del pedido de marketplace."""

    @inject
    def __init__(
        self,
        flujo: PedidoFlujo,
        titularidad: ITitularidadActorService,
        obtencion_persona: IObtensionPersonaService,
    ):
        self.flujo = flujo
        self.titularidad = titularidad
        self.obtencion_persona = obtencion_persona

    async def crear_pedido(
        self,
        usuario,
        data: PedidoCreateData,
    ) -> PedidoCreadoResult:
        """Crea (o recupera) el pedido del actor autenticado.

        Args:
            usuario: la cuenta autenticada (`request.auth`).
            data: los artículos y cantidades declarados.

        Returns:
            El pedido creado o recuperado, con su snapshot congelado.

        Raises:
            `CompradorSinPersonaError`: la cuenta no tiene persona vinculada.
        """
        persona_id = await sync_to_async(self._resolver_comprador)(usuario, data)
        return await self.flujo.crear_pedido(data, persona_id)

    async def obtener_pedido_por_token(
        self,
        token: str,
        usuario,
    ) -> PedidoSeguimientoResult:
        """El pedido de un enlace privado.

        Un actor AUTENTICADO tiene que ser el comprador del pedido; un
        enlace de invitado (sin sesión) se abre con el token, que es la
        credencial del enlace (P-01).
        """
        persona_id = await sync_to_async(self._persona_id)(usuario)
        return await self.flujo.obtener_pedido_por_token(token, persona_id)

    async def confirmar_entrega(self, usuario, pedido_id):
        """Confirma la entrega de un pedido pagado (DOM-06 · RN-M07).

        Es **IDEMPOTENTE**: un reintento del operador devuelve el MISMO
        acta, no la duplica.

        Args:
            usuario: la cuenta que opera (el actor del acta).
            pedido_id: el pedido a entregar.

        Returns:
            El acta de la entrega.
        """
        return await self.flujo.confirmar_entrega(pedido_id, usuario)

    # ── Internos ────────────────────────────────────────────────────────────

    def _persona_id(self, usuario) -> str | None:
        """La persona del actor, o `None` si no hay actor o no tiene."""
        if usuario is None:
            return None
        return self.titularidad.persona_id_del_actor(usuario)

    def _resolver_comprador(self, usuario, data: PedidoCreateData) -> str:
        """Resuelve la identidad en servidor sin crear una cuenta invitada."""
        persona_id = self._persona_id(usuario)
        if persona_id:
            return str(persona_id)
        if usuario is not None and getattr(usuario, "is_authenticated", False):
            raise CompradorSinPersonaError()
        persona = self.obtencion_persona.obtener_o_registrar(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
        )
        return str(persona.id)


__all__ = ["PedidoOrchestrator"]
