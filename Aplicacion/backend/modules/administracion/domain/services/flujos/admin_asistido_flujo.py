"""`AdminAsistidoFlujo` — los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

## La REGLA del Dueño (aplicada a los TRES comandos)

Este flujo **no implementa ninguna regla del dominio**. La EJECUCIÓN la hacen
los módulos DUEÑOS:

| Comando | Dueño del efecto | Dueño de la liquidación |
|---|---|---|
| agregar participante | `salesianos_fest` (`PoolFlujo`) | — |
| comprar pases para un cliente | `salesianos_fest` (`CompraPaseFlujo`) | `pagos` (`AprobarPagoManualFlujo`) |
| comprar un pedido para un cliente | `marketplace` (`PedidoFlujo`) | `pagos` (`AprobarPagoManualFlujo`) |

Aquí sólo se orchestran cuatro cosas:

1. el **MOTIVO**, que se exige antes de tocar nada (422 `MOTIVO_REQUERIDO`);
2. la **IDENTIDAD DEL CLIENTE**, que se resuelve (o se registra) con la
   infraestructura de identidades que ya existe, NUNCA con la cuenta del
   administrador;
3. la **APROBACIÓN DEL PAGO**, que la aplica el dueño del pago con la misma
   evidencia y la misma lógica de liquidación canónica;
4. el **ACTA**, que se escribe después de la acción y la nombra.

## El COMPRADOR QUE NO SE PIERDE

**El COMPRADOR es el CLIENTE, nunca el administrador.** El administrador es el
ACTOR: queda en el acta con QUIÉN, CUÁNDO, QUÉ y POR QUÉ. La compra, el lote
y el pedido se guardan a nombre del cliente (`Compra.persona`,
`CompraPase.comprador`, `Pedido.comprador`).

## Lo que este flujo NO hace

- **NO borra una `Persona`**: ni al agregar ni al retirar. Una retirada es una
  BAJA de `Participacion`, no un borrado.
- **NO reimplementa la transición de estado del pago**: la aprobación llama
  al flujo canónico del dueño y usa su ACTIVACIÓN de derechos.
- **NO copia reglas de elegibilidad**: capacidad, duplicado, disciplina y
  compatibilidad de género los aplica `PoolFlujo`.
"""

from asgiref.sync import sync_to_async
from injector import inject

from core.exceptions import ConflictError, NotFoundError
from modules.administracion.domain.constants import (
    CodigoAccionAdmin,
    EntidadAuditada,
)
from modules.administracion.domain.results.admin_asistido_results import (
    CompraAsistidaResultado,
    ParticipanteAsistidoResultado,
)
from modules.administracion.domain.schemas.admin_asistido_schemas import (
    AsignarParticipanteEquipoData,
    ClienteAsistidoData,
    ComprarPaseParaClienteData,
    ComprarPedidoParaClienteData,
)
from modules.administracion.domain.selectors.admin_operacion_selector import (
    AdminEquipoSelector,
)
from modules.administracion.domain.services.core.admin_accion_sensible_service import (
    AdminAccionSensibleService,
)
from modules.marketplace.domain.schemas.pedido_schemas import (
    PedidoCreateData,
    PedidoItemCreateData,
)
from modules.marketplace.domain.services.flujos.pedido_flujo import PedidoFlujo
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.pagos.domain.services.flujos.aprobar_pago_manual_flujo import (
    AprobarPagoManualFlujo,
)
from modules.salesianos_fest.domain.constants import EstadoParticipacion
from modules.salesianos_fest.domain.exceptions import PersonaNoEncontradaError
from modules.salesianos_fest.domain.ports import (
    IObtensionPersonaService,
    IResolucionPersonaService,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import ComprarPaseData
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.services.flujos.compra_pase_flujo import (
    CompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo


class AdminAsistidoFlujo:
    """Los casos de uso de los comandos administrativos asistidos."""

    @inject
    def __init__(
        self,
        servicio_accion: AdminAccionSensibleService,
        equipo_selector: AdminEquipoSelector,
        pool_flujo: PoolFlujo,
        compra_pase_flujo: CompraPaseFlujo,
        pedido_flujo: PedidoFlujo,
        obtencion_persona: IObtensionPersonaService,
        resolucion_persona: IResolucionPersonaService,
        aprobar_pago_manual_flujo: AprobarPagoManualFlujo,
        estado_operativo_pago: EstadoOperativoPagoService,
    ):
        self.servicio_accion = servicio_accion
        self.equipo_selector = equipo_selector
        self.pool_flujo = pool_flujo
        self.compra_pase_flujo = compra_pase_flujo
        self.pedido_flujo = pedido_flujo
        self.obtencion_persona = obtencion_persona
        self.resolucion_persona = resolucion_persona
        self.aprobar_pago_manual_flujo = aprobar_pago_manual_flujo
        self.estado_operativo_pago = estado_operativo_pago

    # ── Participantes ───────────────────────────────────────────────────────

    async def agregar_participante(
        self,
        actor,
        data: AsignarParticipanteEquipoData,
    ) -> ParticipanteAsistidoResultado:
        """Agrega una persona EXISTENTE a la plantilla de un equipo.

        La persona se identifica por DOCUMENTO EXACTO. Si no está en el
        padrón, el comando falla con 404: agregar un participante NO crea
        una persona nueva (la UI administrativa no expone un CRUD de
        `Persona`).

        Las REGLAS del dueño (capacidad del equipo, duplicado, disciplina
        permitida, compatibilidad de género y saldo de cupos) las aplica
        `PoolFlujo.agregar_participante`: este flujo no las reimplementa.
        """
        motivo = self.servicio_accion.validar_motivo(data.motivo)

        equipo = await sync_to_async(self._obtener_equipo)(data.equipo_id)
        persona = await sync_to_async(self._resolver_persona_existente)(
            data.tipo_documento,
            data.numero_documento,
        )

        await self.pool_flujo.agregar_participante(
            ParticipanteAsignarData(
                inscripcion_id=equipo.inscripcion_id,
                equipo_id=data.equipo_id,
                persona_id=persona.id,
                rol=data.rol,
            )
        )

        participacion = await sync_to_async(self._obtener_participacion)(
            data.equipo_id,
            persona.id,
        )

        await sync_to_async(self.servicio_accion.registrar_acta)(
            actor=actor,
            accion=CodigoAccionAdmin.AGREGAR_PARTICIPANTE_EQUIPO,
            entidad=EntidadAuditada.PARTICIPACION,
            motivo=motivo,
            edicion_id=str(equipo.inscripcion.edicion_id),
            entidad_id=str(participacion.id),
            datos={
                "equipo_id": str(data.equipo_id),
                "inscripcion_id": str(equipo.inscripcion_id),
                "persona_id": str(persona.id),
                "rol": participacion.rol,
            },
        )

        return ParticipanteAsistidoResultado(
            participacion_id=str(participacion.id),
            persona_id=str(persona.id),
            nombre=f"{persona.nombres} {persona.apellidos}".strip(),
            documento=persona.numero_documento,
            equipo_id=str(participacion.equipo_id),
            inscripcion_id=str(participacion.inscripcion_id),
            rol=participacion.rol,
            estado=participacion.estado,
        )

    # ── Compras asistidas ───────────────────────────────────────────────────

    async def comprar_pase_para_cliente(
        self,
        actor,
        data: ComprarPaseParaClienteData,
    ) -> CompraAsistidaResultado:
        """Compra un lote de pases PARA un cliente y registra su pago.

        El lote lo crea el DUEÑO (`CompraPaseFlujo`) con el CLIENTE como
        comprador; el pago lo liquida el DUEÑO del pago
        (`AprobarPagoManualFlujo`) con la evidencia declarada. Este flujo no
        reimplementa ninguna transición de estado.
        """
        motivo = self.servicio_accion.validar_motivo(data.evidencia.motivo)

        cliente = await sync_to_async(self._resolver_cliente)(data.cliente)

        compra = await self.compra_pase_flujo.comprar_pase(
            ComprarPaseData(
                persona_id=str(cliente.id),
                pase_id=str(data.pase_id),
                cantidad=data.cantidad,
                tipo_documento=data.cliente.tipo_documento,
                numero_documento=data.cliente.numero_documento,
                nombres=data.cliente.nombres,
                apellidos=data.cliente.apellidos,
                contacto_email=data.cliente.contacto_email,
            ),
            actor=None,
        )

        await self.aprobar_pago_manual_flujo.aprobar(
            orden_pago_id=compra.orden_pago_id,
            actor_id=str(actor.id),
            canal=data.evidencia.canal,
            referencia=data.evidencia.referencia,
            motivo=motivo,
        )

        estado_pago = await sync_to_async(self._estado_del_pago)(
            compra.orden_pago_id
        )

        await sync_to_async(self.servicio_accion.registrar_acta)(
            actor=actor,
            accion=CodigoAccionAdmin.COMPRAR_PASE_PARA_CLIENTE,
            entidad=EntidadAuditada.COMPRA,
            motivo=motivo,
            edicion_id=compra.edicion_id,
            entidad_id=compra.compra_id,
            datos={
                "compra_pase_id": compra.compra_pase_id,
                "orden_pago_id": compra.orden_pago_id,
                "pase_id": compra.pase_id,
                "cantidad": compra.cantidad,
                "total": str(compra.total),
                "moneda": compra.moneda,
                "comprador_persona_id": compra.comprador_persona_id,
                "canal": data.evidencia.canal,
                "referencia": data.evidencia.referencia,
            },
        )

        return CompraAsistidaResultado(
            compra_id=compra.compra_id,
            recurso_id=compra.compra_pase_id,
            orden_pago_id=compra.orden_pago_id,
            tipo="PASE",
            concepto=compra.pase_nombre,
            total=compra.total,
            moneda=compra.moneda,
            estado=compra.estado,
            estado_pago=estado_pago,
            comprador_persona_id=compra.comprador_persona_id,
            comprador_nombre=compra.comprador_nombres,
            cantidad=compra.cantidad,
        )

    async def comprar_pedido_para_cliente(
        self,
        actor,
        data: ComprarPedidoParaClienteData,
    ) -> CompraAsistidaResultado:
        """Crea un pedido de tienda PARA un cliente y registra su pago.

        El pedido lo crea el DUEÑO (`PedidoFlujo`) con el CLIENTE como
        comprador y con el stock reservado en la MISMA transacción; el pago lo
        liquida el DUEÑO del pago (`AprobarPagoManualFlujo`).
        """
        motivo = self.servicio_accion.validar_motivo(data.evidencia.motivo)

        cliente = await sync_to_async(self._resolver_cliente)(data.cliente)

        pedido = await self.pedido_flujo.crear_pedido(
            PedidoCreateData(
                items=[
                    PedidoItemCreateData(
                        tipo=item.tipo,
                        producto_id=item.producto_id,
                        cantidad=item.cantidad,
                    )
                    for item in data.items
                ],
                tipo_documento=data.cliente.tipo_documento,
                numero_documento=data.cliente.numero_documento,
                nombres=data.cliente.nombres,
                apellidos=data.cliente.apellidos,
                contacto_email=data.cliente.contacto_email,
            ),
            persona_id=str(cliente.id),
        )

        if not pedido.orden_pago_id:
            raise ConflictError(
                "La compra no tiene una orden de pago que registrar.",
                code="PAGO_MANUAL_EVIDENCIA_INVALIDA",
            )

        await self.aprobar_pago_manual_flujo.aprobar(
            orden_pago_id=pedido.orden_pago_id,
            actor_id=str(actor.id),
            canal=data.evidencia.canal,
            referencia=data.evidencia.referencia,
            motivo=motivo,
        )

        estado_pago = await sync_to_async(self._estado_del_pago)(pedido.orden_pago_id)

        await sync_to_async(self.servicio_accion.registrar_acta)(
            actor=actor,
            accion=CodigoAccionAdmin.COMPRAR_PEDIDO_PARA_CLIENTE,
            entidad=EntidadAuditada.PEDIDO,
            motivo=motivo,
            edicion_id=str(pedido.edicion_id),
            entidad_id=str(pedido.id),
            datos={
                "orden_pago_id": pedido.orden_pago_id,
                "total": str(pedido.total),
                "moneda": pedido.moneda,
                "comprador_persona_id": str(cliente.id),
                "canal": data.evidencia.canal,
                "referencia": data.evidencia.referencia,
            },
        )

        return CompraAsistidaResultado(
            compra_id=str(pedido.compra_id or ""),
            recurso_id=str(pedido.id),
            orden_pago_id=pedido.orden_pago_id,
            tipo="PEDIDO",
            concepto=", ".join(linea.concepto_nombre for linea in pedido.lineas),
            total=pedido.total,
            moneda=pedido.moneda,
            estado=pedido.estado,
            estado_pago=estado_pago,
            comprador_persona_id=str(cliente.id),
            comprador_nombre=f"{cliente.nombres} {cliente.apellidos}".strip(),
            cantidad=sum(linea.cantidad for linea in pedido.lineas),
        )

    # ── Internos sync ───────────────────────────────────────────────────────

    def _obtener_equipo(self, equipo_id):
        """El equipo, o 404.

        La inscripción del equipo la declara el DUEÑO del modelo: este flujo
        no la deduce ni la inventa.
        """
        equipo = self.equipo_selector.obtener(equipo_id)
        if equipo is None:
            raise NotFoundError(resource="Equipo", code="RESOURCE_NOT_FOUND")
        return equipo

    def _resolver_persona_existente(self, tipo_documento, numero_documento):
        """La persona del padrón con ese documento EXACTO, o 404.

        Agregar un participante NO crea una persona: la identidad se resuelve
        en el padrón y, si no existe, el comando falla.
        """
        persona = self.resolucion_persona.resolver_por_documento(
            tipo_documento,
            numero_documento,
        )
        if persona is None:
            raise PersonaNoEncontradaError()
        return persona

    def _resolver_cliente(self, cliente: ClienteAsistidoData):
        """La persona del CLIENTE, registrada en el padrón si no existía.

        Es la MISMA infraestructura de identidades que usa el checkout
        invitado: el cliente es una identidad civil y no necesita cuenta.
        """
        return self.obtencion_persona.obtener_o_registrar(
            tipo_documento=cliente.tipo_documento,
            numero_documento=cliente.numero_documento,
            nombres=cliente.nombres,
            apellidos=cliente.apellidos,
        )

    def _obtener_participacion(self, equipo_id, persona_id):
        """La participación ACTIVA que el dueño acaba de crear."""
        from modules.salesianos_fest.domain.models import Participacion

        participacion = (
            Participacion.objects.filter(
                equipo_id=equipo_id,
                persona_id=persona_id,
                estado=EstadoParticipacion.ACTIVA,
            )
            .select_related("persona")
            .order_by("-created_at")
            .first()
        )

        if participacion is None:
            raise NotFoundError(resource="Participación", code="RESOURCE_NOT_FOUND")

        return participacion

    def _estado_del_pago(self, orden_pago_id):
        """El VEREDICTO del pago, calculado por su dueño.

        `EstadoOperativoPagoService` es el único dueño de ese veredicto: este
        flujo lo copia y no vuelve a cruzar los hechos del pago.
        """
        from modules.pagos.domain.models import OrdenPago

        orden = OrdenPago.objects.filter(id=orden_pago_id).first()
        veredicto = self.estado_operativo_pago.calcular_para_orden(orden)
        return veredicto.codigo


__all__ = ["AdminAsistidoFlujo"]
