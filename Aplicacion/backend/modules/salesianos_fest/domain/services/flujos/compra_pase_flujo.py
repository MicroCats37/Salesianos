"""`CompraPaseFlujo` — la compra de un lote de pases, CON o SIN cuenta.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC,
ABREN `transaction.atomic()`.

Este flujo implementa `FL-06` ("Comprar pase sin cuenta") y las reglas
congeladas que lo acompañan.

**RN-C02 — El servidor congela el precio.** El precio lo resuelve el
servidor contra el catálogo vigente; el cliente NO declara ningún importe.

**RN-P02 — Una compra pendiente NO habilita ningún derecho.** El lote nace
`PENDIENTE` y su capacidad asignable es CERO. Los pases se pueden asignar
sólo cuando la ACTIVACIÓN de derechos (FND-05) marca el lote como `PAGADA`.

**FL-06 paso 2 — La compra NO obliga a crear un `Usuario`.** El comprador es
una identidad CIVIL (`Persona`), que existe sin cuenta (`FR-03` §1.1). Este
flujo NUNCA toca `usuarios.Usuario`.

**RN-P04 — El comprador y quien asiste pueden ser personas distintas.** Este
flujo no asigna beneficiarios: sólo compra el lote. La asignación es otra
operación, sobre la capacidad pagada.

**TITULARIDAD.** Si la petición va AUTENTICADA, el comprador es el ACTOR: el
documento del payload se IGNORA. Si la petición es de un INVITADO, el
comprador es la identidad civil declarada, y se registra en el padrón si no
existía. Un documento NUNCA es una credencial (`RN-U04`).
"""

from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.schemas.compra_schemas import (
    CompraCreateData,
    LineaCompraSnapshot,
    calcular_total,
)
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo
from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.constants import (
    CONCEPTO_LINEA_PASE,
    CausaOperativaCompraPase,
    EstadoPase,
    MAX_PASES_POR_COMPRA,
    MIN_PASES_POR_COMPRA,
)
from modules.salesianos_fest.domain.exceptions import (
    CantidadInvalidaError,
    CompradorSinPersonaError,
    PaseNoDisponibleError,
)
from modules.salesianos_fest.domain.ports import (
    IAlcanceEdicionService,
    IObtensionPersonaService,
    ITitularidadService,
)
from modules.salesianos_fest.domain.referencia_pase import referencia_compra_pase
from modules.salesianos_fest.domain.results.pase_result import CompraPaseResultado
from modules.salesianos_fest.domain.schemas.pase_schemas import ComprarPaseData
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_core_service import (
    PaseCoreService,
)


class CompraPaseFlujo:
    """La compra de un lote de pases."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        pase_core: PaseCoreService,
        alcance_edicion: IAlcanceEdicionService,
        obtencion_persona: IObtensionPersonaService,
        titularidad: ITitularidadService,
        compra_flujo: CompraFlujo,
    ):
        self.pase_selector = pase_selector
        self.pase_core = pase_core
        self.alcance_edicion = alcance_edicion
        self.obtencion_persona = obtencion_persona
        self.titularidad = titularidad
        self.compra_flujo = compra_flujo

    async def comprar_pase(
        self,
        data: ComprarPaseData,
        actor=None,
    ) -> CompraPaseResultado:
        """Crea (o recupera) la compra pendiente de un lote de pases.

        Returns:
            El lote comprado, su compra y su token de gestión. El lote queda
            `PENDIENTE`: todavía NO se puede asignar ningún beneficiario
            (`RN-P02`).
        """
        edicion = await sync_to_async(self._resolver_edicion)(None)
        await sync_to_async(self._validar_cantidad)(data.cantidad)
        pase = await sync_to_async(self._resolver_pase)(edicion, data.pase_id)
        precio = await sync_to_async(self._resolver_precio)(pase)
        comprador_id = await sync_to_async(self._resolver_comprador)(data, actor)

        referencia = referencia_compra_pase(
            edicion_id=edicion.id,
            pase_id=pase.id,
            comprador_id=comprador_id,
            cantidad=data.cantidad,
        )
        total = await sync_to_async(self._calcular_total)(precio.monto, data.cantidad)

        intencion = CompraCreateData(
            persona_id=comprador_id,
            origen=OrigenCompra.PASE,
            lineas=[
                LineaCompraSnapshot(
                    concepto_tipo=CONCEPTO_LINEA_PASE,
                    concepto_id=str(pase.id),
                    concepto_nombre=pase.nombre,
                    cantidad=data.cantidad,
                    precio_unitario=precio.monto,
                    precio_aplicado=precio.monto,
                )
            ],
            referencia=referencia,
            moneda=precio.moneda,
        )

        compra, compra_reutilizada = await self.compra_flujo.crear_o_reutilizar_compra(
            intencion
        )
        compra_pase, lote_reutilizado = await sync_to_async(
            self._recuperar_o_crear_lote
        )(
            compra,
            edicion,
            pase,
            comprador_id,
            data,
            precio,
            total,
            referencia,
        )

        reutilizada = compra_reutilizada or lote_reutilizado
        return await sync_to_async(self._construir_resultado)(
            compra_pase,
            compra,
            reutilizada,
        )

    @staticmethod
    def _construir_resultado(
        compra_pase,
        compra,
        reutilizada: bool,
    ) -> CompraPaseResultado:
        """Proyecta las relaciones ORM antes de volver al contexto async."""
        return CompraPaseResultado(
            compra_pase_id=str(compra_pase.id),
            compra_id=str(compra.id),
            orden_pago_id=str(compra.orden_pago_id) if compra.orden_pago_id else "",
            estado=compra_pase.estado,
            cantidad=compra_pase.cantidad,
            precio_unitario=compra_pase.precio_unitario,
            total=compra_pase.total,
            moneda=compra_pase.moneda,
            pase_id=str(compra_pase.pase_id),
            pase_nombre=compra_pase.pase.nombre,
            edicion_id=str(compra_pase.edicion_id),
            edicion_nombre=compra_pase.edicion.nombre,
            comprador_persona_id=str(compra_pase.comprador_id),
            comprador_nombres=compra_pase.comprador.nombres,
            token=compra_pase.token,
            token_expira_en=compra_pase.token_expira_en,
            reutilizada=reutilizada,
            causa_operativa=(
                CausaOperativaCompraPase.COMPRA_PASE_REUTILIZADA
                if reutilizada
                else CausaOperativaCompraPase.COMPRA_PASE_CREADA
            ),
        )

    # ── Internos (sync) ─────────────────────────────────────────────────────

    def _resolver_edicion(self, edicion_id):
        """Resuelve la edición del alcance y exige el módulo `pases`.

        Sin `edicion_id` explícito se aplican los niveles 2 → 3 → 4 del orden
        congelado (`FR-02` §2.2). En ninguno hay fallback informal.
        """
        if edicion_id:
            edicion = self.alcance_edicion.resolver_explicita(
                edicion_id,
                exigir_publicada=True,
            )
        else:
            edicion = self.alcance_edicion.resolver_actual(
                exigir_publicada=True,
                permitir_publicada_por_defecto=True,
            )
        if not edicion.modulo_habilitado(ModuloLogico.PASES):
            raise ModuloNoHabilitadoError()
        return edicion

    @staticmethod
    def _validar_cantidad(cantidad: int) -> None:
        """La cantidad está dentro de los límites de dominio."""
        if cantidad < MIN_PASES_POR_COMPRA or cantidad > MAX_PASES_POR_COMPRA:
            raise CantidadInvalidaError()

    def _resolver_pase(self, edicion, pase_id):
        """El pase VIGENTE de la edición, con precio vigente.

        Sin precio vigente NO hay venta: no se inventa un importe de reserva
        (`FL-01` paso 3, aplicado al catálogo de pases).
        """
        pase = self.pase_selector.obtener_pase(edicion.id, pase_id)
        if pase is None or pase.estado != EstadoPase.VIGENTE:
            raise PaseNoDisponibleError()
        return pase

    def _resolver_precio(self, pase):
        """El precio vigente del pase."""
        precio = self.pase_selector.obtener_precio_vigente(pase.id)
        if precio is None:
            raise PaseNoDisponibleError()
        return precio

    @staticmethod
    def _calcular_total(precio_unitario, cantidad: int) -> Decimal:
        """El total CONGELADO: la MISMA expresión que usa `commerce`.

        Se usa `calcular_total` de `commerce` para que el total del lote y
        el total de la compra coincidan EXACTAMENTE: es la misma regla
        (`RN-C02`), escrita una sola vez.
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

    def _resolver_comprador(self, data: ComprarPaseData, actor) -> str:
        """La identidad del COMPRADOR.

        - Actor AUTENTICADO → el comprador es el actor. El documento del
          payload se IGNORA: el servidor decide quién compra.
        - INVITADO → el comprador es la identidad civil declarada; se
          REGISTRA en el padrón si no existía. Nunca se crea una CUENTA.
        """
        if actor is not None and getattr(actor, "is_authenticated", False):
            persona_id = self.titularidad.persona_id_del_actor(actor)
            if not persona_id:
                raise CompradorSinPersonaError()
            return str(persona_id)

        persona = self.obtencion_persona.obtener_o_registrar(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
        )
        return str(persona.id)

    @transaction.atomic()
    def _recuperar_o_crear_lote(
        self,
        compra,
        edicion,
        pase,
        comprador_id,
        data: ComprarPaseData,
        precio,
        total,
        referencia,
    ):
        """El lote de pases de esa compra, o el que se crea.

        Returns:
            La tupla `(compra_pase, reutilizado)`.
        """
        existente = self.pase_selector.obtener_compra_pase_por_compra(compra.id)
        if existente is not None:
            return existente, True

        try:
            lote = self.pase_core.crear_compra_pase(
                edicion_id=edicion.id,
                pase_id=pase.id,
                comprador_id=comprador_id,
                cantidad=data.cantidad,
                precio_unitario=precio.monto,
                total=total,
                moneda=precio.moneda,
                referencia=referencia,
                contacto_email=data.contacto_email,
                compra_id=compra.id,
            )
        except IntegrityError:
            # Carrera: otra petición idéntica creó el lote primero. La fila
            # ganadora es la buena.
            ganador = self.pase_selector.obtener_compra_pase_por_compra(compra.id)
            if ganador is None:
                raise
            return ganador, True
        return lote, False


__all__ = ["CompraPaseFlujo"]
