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

## El ALTA de participante es UNA unidad de trabajo

El alta de un participante es la ÚNICA operación de este flujo que puede
dejar BASURA si falla a medias: registrar una identidad y luego ser
rechazado por una regla del dueño deja una `Persona` que nadie pidió.

Por eso el alta ocurre DENTRO de UNA transacción: la identidad se resuelve,
se registra o se corrige, el dueño aplica sus reglas, el cupo se reserva y
el acta se escribe. Si CUALQUIER paso falla, el conjunto se deshace entero.

Para llamar a las reglas del dueño SIN partir esa transacción, el flujo usa
la entrada SÍNCRONA del dueño (`PoolFlujo.agregar_participante_sync`): las
reglas NO se duplican y el `await` NO cruza los límites de la transacción.

## Lo que este flujo NO hace

- **NO borra una `Persona`**: ni al agregar ni al retirar. Una retirada es una
  BAJA de `Participacion`, no un borrado.
- **NO crea una CUENTA**: la identidad que se registra es una `Persona` sin
  `Usuario`. El padrón de identidades es el dueño y su servicio de dominio
  (`IObtensionPersonaService`) no toca las cuentas.
- **NO reescribe los nombres de una identidad existente**: si la persona ya
  está en el padrón, sus nombres y sus apellidos son los del padrón. Los
  datos declarados por el administrador sólo se usan al REGISTRARLA.
- **NO inventa el género**: lo único que puede corregir de una identidad
  existente es el GÉNERO, y sólo cuando el administrador lo declara
  EXPLÍCITAMENTE (`M` o `F`) y es DISTINTO del almacenado. Nunca se infiere
  de la disciplina ni del equipo.
- **NO reimplementa la transición de estado del pago**: la aprobación llama
  al flujo canónico del dueño y usa su ACTIVACIÓN de derechos.
- **NO copia reglas de elegibilidad**: capacidad, duplicado, disciplina y
  compatibilidad de género los aplica `PoolFlujo`.
"""

import hashlib
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from injector import inject

from core.exceptions import ConflictError, NotFoundError, UnprocessableEntityError
from modules.administracion.domain.constants import (
    CodigoAccionAdmin,
    EntidadAuditada,
)
from modules.administracion.domain.results.admin_asistido_results import (
    CompraAsistidaResultado,
    CotizacionPaseClienteResultado,
    ParticipanteAsistidoResultado,
)
from modules.administracion.domain.schemas.admin_asistido_schemas import (
    AsignarParticipanteEquipoData,
    ClienteAsistidoData,
    ComprarPaseParaClienteData,
    ComprarPedidoParaClienteData,
    CotizarPaseParaClienteData,
    IdentidadAsistidaData,
)
from modules.administracion.domain.selectors.admin_operacion_selector import (
    AdminEquipoSelector,
)
from modules.administracion.domain.services.core.admin_accion_sensible_service import (
    AdminAccionSensibleService,
)
from modules.commerce.domain.schemas.compra_schemas import (
    LineaCompraSnapshot,
    calcular_total,
)
from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
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
from modules.salesianos_fest.domain.constants import (
    CONCEPTO_LINEA_PASE,
    MAX_PASES_POR_COMPRA,
    MIN_PASES_POR_COMPRA,
    EstadoPase,
    EstadoParticipacion,
)
from modules.salesianos_fest.domain.exceptions import (
    CantidadInvalidaError,
    PaseNoDisponibleError,
    PaseNoEncontradoError,
    PrecioCambiadoError,
)
from modules.salesianos_fest.domain.ports import (
    IAlcanceEdicionService,
    ICorreccionGeneroPersonaService,
    IObtensionPersonaService,
    IResolucionPersonaService,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import ComprarPaseData
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.flujos.compra_pase_flujo import (
    CompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo

#: Las horas de validez de una cotización de pase.
#:
#: Mismo precedente que la cotización de paquetes
#: (`VIGENCIA_COTIZACION_HORAS` en `CatalogoFlujo`): la cotización es
#: EFÍMERA y no se persiste.
VIGENCIA_COTIZACION_HORAS = 24

#: El estado de una cotización vigente.
ESTADO_COTIZACION_ACTIVA = "ACTIVA"


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
        correccion_genero: ICorreccionGeneroPersonaService,
        aprobar_pago_manual_flujo: AprobarPagoManualFlujo,
        estado_operativo_pago: EstadoOperativoPagoService,
        pase_selector: PaseSelector,
        alcance_edicion: IAlcanceEdicionService,
    ):
        self.servicio_accion = servicio_accion
        self.equipo_selector = equipo_selector
        self.pool_flujo = pool_flujo
        self.compra_pase_flujo = compra_pase_flujo
        self.pedido_flujo = pedido_flujo
        self.obtencion_persona = obtencion_persona
        self.resolucion_persona = resolucion_persona
        self.correccion_genero = correccion_genero
        self.aprobar_pago_manual_flujo = aprobar_pago_manual_flujo
        self.estado_operativo_pago = estado_operativo_pago
        self.pase_selector = pase_selector
        self.alcance_edicion = alcance_edicion

    # ── Participantes ───────────────────────────────────────────────────────

    async def agregar_participante(
        self,
        actor,
        data: AsignarParticipanteEquipoData,
    ) -> ParticipanteAsistidoResultado:
        """Agrega una persona a la plantilla de un equipo.

        La persona se identifica por DOCUMENTO EXACTO. Si ya está en el
        padrón, se REUTILIZA tal cual (sus Nombres y sus apellidos nunca se
        reescriben); si NO está, se REGISTRA como identidad civil —**sin
        cuenta**— con los nombres, los apellidos y el género declarados, y
        recién después se la agrega al equipo.

        El ÚNICO dato de una identidad existente que este comando puede
        corregir es el GÉNERO, y sólo cuando el administrador lo declara
        EXPLÍCITAMENTE (`M` o `F`) y es DISTINTO del almacenado.

        La UI administrativa no expone un CRUD de `Persona`: este comando no
        borra ninguna, no edita sus nombres y nunca crea una CUENTA.

        Las REGLAS del dueño (capacidad del equipo, duplicado, disciplina
        permitida, compatibilidad de género y saldo de cupos) las aplica
        `PoolFlujo`: este flujo no las reimplementa.

        ## La unidad de trabajo

        Todo lo que puede fallar ocurre DENTRO de UNA transacción
        (`_agregar_participante_atomico`): resolver o registrar la
        identidad, corregir su género, aplicar las reglas del dueño,
        reservar el cupo y escribir el acta. Si CUALQUIER paso falla, el
        conjunto se deshace: no queda una `Persona` huérfana, ni un cupo
        reservado, ni una participación sin auditar.
        """
        motivo = self.servicio_accion.validar_motivo(data.motivo)

        equipo = await sync_to_async(self._obtener_equipo)(data.equipo_id)

        return await sync_to_async(self._agregar_participante_atomico)(
            actor,
            data,
            equipo,
            motivo,
        )

    # ── Compras asistidas ───────────────────────────────────────────────────

    async def cotizar_pase_para_cliente(
        self,
        data: CotizarPaseParaClienteData,
    ) -> CotizacionPaseClienteResultado:
        """COTIZA un lote de pases: el precio y el total los deriva el servidor.

        Es una LECTURA: no persiste nada y no toca el dinero. El precio
        vigente lo resuelve el DUEÑO (`PaseSelector`) contra el catálogo de
        la edición; el total lo deriva el servidor con la MISMA expresión que
        usa `commerce` para congelar la compra (`RN-C02`).

        El `version` que devuelve es el TOKEN DE CONCURRENCIA del precio: si
        el catálogo se movió, el token cambia y el alta posterior se rechaza
        con 409 `PRECIO_CAMBIADO`.
        """
        return await sync_to_async(self._cotizar_pase)(data.pase_id, data.cantidad)

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

        El `monto_declarado` viaja como EVIDENCIA AUDITADA: lo guarda el
        dueño del pago y NO toca el total canónico, ni el estado del pago, ni
        el de la compra.
        """
        motivo = self.servicio_accion.validar_motivo(data.evidencia.motivo)

        # El PRECIO OBSOLETO se comprueba ANTES de tocar nada: si el
        # catálogo se movió desde la cotización, el comando se rechaza y no
        # se crea ni la compra, ni la orden, ni el pago, ni la identidad.
        if data.evidencia.precio_version:
            await sync_to_async(self._validar_precio_vigente)(
                data.pase_id,
                data.evidencia.precio_version,
            )

        cliente = await sync_to_async(self._resolver_cliente)(data.cliente)

        compra = await self.compra_pase_flujo.comprar_pase(
            ComprarPaseData(
                persona_id=str(cliente.id),
                pase_id=str(data.pase_id),
                cantidad=data.cantidad,
                # La identidad del COMPRADOR es la del PADRÓN: el documento y
                # los nombres canónicos son los de la `Persona` resuelta, no
                # los declarados por el administrador.
                tipo_documento=cliente.tipo_documento,
                numero_documento=cliente.numero_documento,
                nombres=cliente.nombres,
                apellidos=cliente.apellidos,
                contacto_email=data.cliente.contacto_email or "",
            ),
            actor=None,
        )

        aprobacion = await self.aprobar_pago_manual_flujo.aprobar(
            orden_pago_id=compra.orden_pago_id,
            actor_id=str(actor.id),
            canal=data.evidencia.canal,
            referencia=data.evidencia.referencia,
            motivo=motivo,
            monto_declarado=data.evidencia.monto_declarado,
            precio_version=data.evidencia.precio_version,
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
                # El importe declarado y el token de precio son EVIDENCIA:
                # se auditan, no calculan nada.
                "monto_declarado": (
                    str(aprobacion.monto_declarado)
                    if getattr(aprobacion, "monto_declarado", None) is not None
                    else None
                ),
                "precio_version": data.evidencia.precio_version or None,
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
            monto_declarado=getattr(aprobacion, "monto_declarado", None),
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
                # La identidad del COMPRADOR es la del PADRÓN: el documento y
                # los nombres canónicos son los de la `Persona` resuelta.
                tipo_documento=cliente.tipo_documento,
                numero_documento=cliente.numero_documento,
                nombres=cliente.nombres,
                apellidos=cliente.apellidos,
                contacto_email=data.cliente.contacto_email or "",
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

    def _cotizar_pase(self, pase_id, cantidad: int) -> CotizacionPaseClienteResultado:
        """La cotización del pase, contra el catálogo vigente.

        El precio lo resuelve el DUEÑO (`PaseSelector`) y el total lo deriva
        el servidor con la MISMA expresión con la que `commerce` congela la
        compra: la cotización y la compra dicen EXACTAMENTE lo mismo.
        """
        if cantidad < MIN_PASES_POR_COMPRA or cantidad > MAX_PASES_POR_COMPRA:
            raise CantidadInvalidaError()

        edicion = self._resolver_edicion()
        pase = self.pase_selector.obtener_pase(edicion.id, pase_id)
        if pase is None:
            raise PaseNoEncontradoError()
        if pase.estado != EstadoPase.VIGENTE:
            raise PaseNoDisponibleError()

        precio = self.pase_selector.obtener_precio_vigente(pase.id)
        if precio is None:
            # Sin precio vigente NO hay venta: no se inventa un importe de
            # reserva.
            raise ConflictError(code="PASE_PRECIO_NO_VIGENTE")

        total = self._calcular_total(precio.monto, cantidad)

        return CotizacionPaseClienteResultado(
            pase_id=str(pase.id),
            edicion_id=str(edicion.id),
            pase_nombre=pase.nombre,
            cantidad=cantidad,
            precio_unitario=precio.monto,
            total=total,
            moneda=precio.moneda,
            version=self._version_del_precio(pase.id, precio),
            estado=ESTADO_COTIZACION_ACTIVA,
            validez_hasta=timezone.now()
            + timedelta(hours=VIGENCIA_COTIZACION_HORAS),
        )

    def _validar_precio_vigente(self, pase_id, precio_version: str) -> None:
        """El token de precio declarado, o el 409 que lo invalida.

        La comprobación es TOLERANTE a propósito: si el pase no se puede
        resolver o no tiene precio vigente, el DUEÑO de la compra lo rechaza
        con SU propio código (`PASE_NO_DISPONIBLE`). Este flujo no inventa un
        código nuevo para el mismo hecho.

        Sin token (`precio_version` vacío) NO hay comprobación: el precio
        vigente es el que rige (`RN-C02`).
        """
        edicion = self._resolver_edicion()
        pase = self.pase_selector.obtener_pase(edicion.id, pase_id)
        if pase is None or pase.estado != EstadoPase.VIGENTE:
            return

        precio = self.pase_selector.obtener_precio_vigente(pase.id)
        if precio is None:
            return

        if self._version_del_precio(pase.id, precio) != precio_version:
            raise PrecioCambiadoError()

    def _resolver_edicion(self):
        """La edición del alcance, con el módulo `pases` habilitado.

        Aplica el ORDEN CONGELADO de la resolución (`FR-02` §2.2) sin
        `edicion_id` explícito: la edición actual y, si procede, la publicada
        por defecto. Es la MISMA resolución que aplica el dueño del catálogo
        (`PaseFlujo`, `CompraPaseFlujo`): la cotización y la compra tienen que
        mirar la MISMA edición.
        """
        edicion = self.alcance_edicion.resolver_actual(
            exigir_publicada=True,
            permitir_publicada_por_defecto=True,
        )
        if not edicion.modulo_habilitado(ModuloLogico.PASES):
            raise ModuloNoHabilitadoError()
        return edicion

    @staticmethod
    def _version_del_precio(pase_id, precio) -> str:
        """El TOKEN DE CONCURRENCIA del precio.

        Identifica la fila de precio exacta que rigió: si el catálogo se movió
        (monto, moneda o ventana de vigencia), el token cambia y el alta se
        rechaza con 409 `PRECIO_CAMBIADO` en vez de cobrar una cantidad que
        nadie vio.
        """
        semilla = (
            f"{pase_id}|{precio.vigente_desde.isoformat()}|"
            f"{precio.monto}|{precio.moneda}"
        )
        return hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _calcular_total(precio_unitario, cantidad: int) -> Decimal:
        """El total DERIVADO por el servidor.

        Es la MISMA expresión de `commerce` que congela la compra
        (`RN-C02`): la regla está escrita una sola vez y la cotización no
        puede discrepar del total que se va a cobrar.
        """
        return calcular_total(
            [
                LineaCompraSnapshot(
                    concepto_tipo=CONCEPTO_LINEA_PASE,
                    concepto_id="0",
                    concepto_nombre="",
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    precio_aplicado=precio_unitario,
                )
            ]
        )

    @transaction.atomic()
    def _agregar_participante_atomico(self, actor, data, equipo, motivo):
        """La unidad de trabajo del alta: UNA SOLA TRANSACCIÓN.

        Aquí ocurre TODO lo que puede fallar del comando:

        1. la IDENTIDAD se resuelve, se REGISTRA o se CORRIGE;
        2. el DUEÑO aplica sus reglas y reserva el cupo;
        3. el ACTA se escribe.

        Si CUALQUIER paso falla —el género no es elegible, la disciplina no
        está permitida, la persona ya participa, el equipo está lleno, no
        hay cupos pagados o el acta no se puede escribir— la transacción se
        deshace ENTERA: no queda una `Persona` recién creada, ni un género
        corregido, ni un cupo reservado, ni una participación sin auditar.

        Es un método SYNC a propósito: la transacción se abre y se cierra
        dentro de él, así que ningún `await` puede cruzar sus límites
        (`contract/django-app-architecture-contract.md` §4.4).
        """
        persona, identidad_registrada, genero_anterior, genero_nuevo = (
            self._resolver_identidad(data)
        )

        self.pool_flujo.agregar_participante_sync(
            ParticipanteAsignarData(
                inscripcion_id=equipo.inscripcion_id,
                equipo_id=data.equipo_id,
                persona_id=persona.id,
                rol=data.rol,
            )
        )

        participacion = self._obtener_participacion(data.equipo_id, persona.id)

        datos = {
            "equipo_id": str(data.equipo_id),
            "inscripcion_id": str(equipo.inscripcion_id),
            "persona_id": str(persona.id),
            "rol": participacion.rol,
            "identidad_registrada": identidad_registrada,
        }

        # La corrección del género queda en el ACTA: el ACTA dice lo que
        # pasó. No setravela ningún otro dato de la identidad.
        if genero_anterior != genero_nuevo:
            datos["genero_anterior"] = genero_anterior
            datos["genero_nuevo"] = genero_nuevo

        self.servicio_accion.registrar_acta(
            actor=actor,
            accion=CodigoAccionAdmin.AGREGAR_PARTICIPANTE_EQUIPO,
            entidad=EntidadAuditada.PARTICIPACION,
            motivo=motivo,
            edicion_id=str(equipo.inscripcion.edicion_id),
            entidad_id=str(participacion.id),
            datos=datos,
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

    def _obtener_equipo(self, equipo_id):
        """El equipo, o 404.

        La inscripción del equipo la declara el DUEÑO del modelo: este flujo
        no la deduce ni la inventa.
        """
        equipo = self.equipo_selector.obtener(equipo_id)
        if equipo is None:
            raise NotFoundError(resource="Equipo", code="RESOURCE_NOT_FOUND")
        return equipo

    def _resolver_identidad(self, identidad: IdentidadAsistidaData):
        """La `Persona` de la identidad declarada: se REUTILIZA o se REGISTRA.

        Es la MISMA infraestructura de identidades que usa el checkout
        invitado: la identidad civil no necesita cuenta y este comando NUNCA
        crea un `Usuario`.

        - Si la persona YA está en el padrón, se devuelve ESA `Persona` y sus
          Nombres y sus apellidos NO se reescriben: la identidad del padrón
          es la autoridad. Lo ÚNICO que puede corregirse es el GÉNERO, y
          sólo si el administrador lo declara EXPLÍCITAMENTE.
        - Si NO está, se REGISTRA con los nombres, los apellidos y el género
          declarados. La normalización EXACTA del documento y la carrera las
          aplica el servicio de dominio: si otra petición registró la
          identidad primero, devuelve la fila que GANÓ.

        Returns:
            La tupla `(persona, identidad_registrada, genero_anterior,
            genero_nuevo)`. `identidad_registrada` dice si la identidad hubo
            que registrarla; los dos géneros dicen qué cambió (y son
            iguales cuando no cambió nada).
        """
        existente = self.resolucion_persona.resolver_por_documento(
            identidad.tipo_documento,
            identidad.numero_documento,
        )
        if existente is not None:
            genero_anterior, genero_nuevo = self._corregir_genero(
                existente,
                identidad.genero,
            )
            return existente, False, genero_anterior, genero_nuevo

        if not (identidad.nombres or "").strip():
            raise UnprocessableEntityError(
                "La identidad no existe en el padrón y necesita nombres para "
                "registrarse.",
                code="VALIDATION_ERROR",
            )

        persona = self.obtencion_persona.obtener_o_registrar(
            tipo_documento=identidad.tipo_documento,
            numero_documento=identidad.numero_documento,
            nombres=identidad.nombres,
            apellidos=identidad.apellidos or "",
            genero=identidad.genero or "",
        )
        return persona, True, "", ""

    def _corregir_genero(self, persona, genero_declarado: str) -> tuple[str, str]:
        """Corrige el GÉNERO de una identidad existente, si se declara otro.

        La corrección es EXPLÍCITA y MÍNIMA:

        - SIN género declarado (`""` o `None`) → se CONSERVA el almacenado.
        - Con `M` o `F` declarado y DISTINTO del almacenado → se actualiza
          SÓLO el campo `genero`, antes de que el dueño valide la
          elegibilidad.
        - Con `M` o `F` declarado e IGUAL al almacenado → no hay nada que
          corregir.

        El género NUNCA se infiere de la disciplina ni del equipo: sólo
        cambia cuando alguien lo declara.

        Returns:
            La tupla `(genero_anterior, genero_nuevo)`. Si no hubo
            corrección, ambos valores son el género almacenado.
        """
        declarado = (genero_declarado or "").strip().upper()

        if not declarado:
            return "", ""

        return self.correccion_genero.corregir_genero(persona, declarado)

    def _resolver_cliente(self, cliente: ClienteAsistidoData):
        """La persona del CLIENTE, registrada en el padrón si no existía.

        Es la MISMA infraestructura de identidades que usa el checkout
        invitado: el cliente es una identidad civil y no necesita cuenta.

        Los nombres, los apellidos y el género del CLIENTE sólo se usan si la
        identidad hay que REGISTRARLA: cuando ya existe, el padrón manda.
        """
        existente = self.resolucion_persona.resolver_por_documento(
            cliente.tipo_documento,
            cliente.numero_documento,
        )
        if existente is not None:
            return existente

        if not (cliente.nombres or "").strip():
            raise UnprocessableEntityError(
                "La identidad no existe en el padrón y necesita nombres para "
                "registrarse.",
                code="VALIDATION_ERROR",
            )

        return self.obtencion_persona.obtener_o_registrar(
            tipo_documento=cliente.tipo_documento,
            numero_documento=cliente.numero_documento,
            nombres=cliente.nombres,
            apellidos=cliente.apellidos or "",
            genero=cliente.genero or "",
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
