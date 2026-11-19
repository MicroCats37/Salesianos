"""`CompraCuposFlujo` — la compra de cupos EXTRA de una inscripción.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

Este flujo implementa `FL-04` ("Ampliar cupos de inscripción") y las reglas
congeladas que lo acompañan:

**RN-C01 — Cada dominio tiene su propio flujo de compra.** La ampliación la
compra `commerce` a través de su interfaz CONGELADA (`CompraFlujo`), con el
origen `INSCRIPCION`. No existe un checkout transversal.

**RN-C02 — El servidor congela el precio.** El precio lo resuelve el
servidor contra el catálogo vigente; el cliente NO declara ningún importe.
La cantidad SÍ la declara el cliente (es lo que se compra), pero está
acotada por los límites de dominio.

**RN-I02 — Una compra pendiente NO habilita cupos.** El flujo crea la
compra PENDIENTE y NO toca `cupos_pagados`: eso lo hace la ACTIVACIÓN de
derechos (FND-05), cuando el pago está confirmado. La ampliación "afecta a
la misma inscripción exactamente una vez" porque la activación es
idempotente por clave (`QA-I02`, `QA-I03`).

**La ampliación es una COMPRA SEPARADA** (`FL-04` paso 2): no reutiliza la
compra del alta, tiene su propia referencia de intención y su propia orden
de pago. Un reintento con la misma cantidad reutiliza la compra PENDIENTE
(`FR-04` I-4); una compra ya pagada no bloquea una nueva.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.schemas.compra_schemas import (
    CompraCreateData,
    LineaCompraSnapshot,
)
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo
from modules.salesianos_fest.domain.constants import (
    CONCEPTO_LINEA_CUPO,
    CausaOperativaCompraCupos,
    EstadoPaquete,
    MAX_CUPOS_POR_AMPLIACION,
    MIN_CUPOS_POR_AMPLIACION,
)
from modules.salesianos_fest.domain.exceptions import (
    CupoInvalidoError,
    InscripcionNoEncontradaError,
    PaqueteNoVigenteError,
)
from modules.salesianos_fest.domain.referencia import referencia_expansion
from modules.salesianos_fest.domain.results.pool_result import CompraCuposResult
from modules.salesianos_fest.domain.schemas.pool_schemas import CompraCuposData
from modules.salesianos_fest.domain.selectors.catalogo_selector import (
    CatalogoSelector,
)
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)


class CompraCuposFlujo:
    """La compra de cupos extra de una inscripción."""

    @inject
    def __init__(
        self,
        inscripcion_selector: InscripcionSelector,
        catalogo_selector: CatalogoSelector,
        compra_flujo: CompraFlujo,
    ):
        self.inscripcion_selector = inscripcion_selector
        self.catalogo_selector = catalogo_selector
        self.compra_flujo = compra_flujo

    async def obtener_responsable(self, inscripcion_id) -> str:
        """El identificador de la persona responsable de la inscripción.

        Lo consulta el ORQUESTADOR para comprobar la titularidad ANTES de
        tocar nada (`FR-03` §2.1). Si la inscripción no existe, se lanza el
        error de dominio: no se inventa una titularidad.
        """
        inscripcion = await sync_to_async(self._obtener_inscripcion)(inscripcion_id)
        return str(inscripcion.responsable_id)

    async def comprar_cupos(self, data: CompraCuposData) -> CompraCuposResult:
        """Crea (o reutiliza) la compra pendiente de los cupos extra.

        Returns:
            La compra y el estado de capacidad de la inscripción. La
            capacidad NO cambia: los cupos se habilitan al activarse el
            pago (`RN-I02`).
        """
        inscripcion = await sync_to_async(self._obtener_inscripcion)(
            data.inscripcion_id
        )
        await sync_to_async(self._validar_cantidad)(data.cantidad)
        paquete = await sync_to_async(self._resolver_paquete)(inscripcion)
        precio = await sync_to_async(self._resolver_precio)(paquete)

        intencion = CompraCreateData(
            persona_id=inscripcion.responsable_id,
            origen=OrigenCompra.INSCRIPCION,
            lineas=[
                LineaCompraSnapshot(
                    concepto_tipo=CONCEPTO_LINEA_CUPO,
                    concepto_id=str(paquete.id),
                    concepto_nombre=paquete.nombre,
                    cantidad=data.cantidad,
                    precio_unitario=precio.monto,
                    precio_aplicado=precio.monto,
                )
            ],
            referencia=referencia_expansion(inscripcion.id, data.cantidad),
            moneda=precio.moneda,
        )
        compra, reutilizada = await self.compra_flujo.crear_o_reutilizar_compra(
            intencion
        )

        return CompraCuposResult(
            inscripcion_id=str(inscripcion.id),
            compra_id=str(compra.id),
            orden_pago_id=str(compra.orden_pago_id),
            estado=compra.estado,
            total=compra.total,
            moneda=compra.moneda,
            cupos_solicitados=data.cantidad,
            cupos_pagados=inscripcion.cupos_pagados,
            cupos_asignados=inscripcion.cupos_asignados,
            cupos_disponibles=max(
                inscripcion.cupos_pagados - inscripcion.cupos_asignados,
                0,
            ),
            reutilizada=reutilizada,
            causa_operativa=(
                CausaOperativaCompraCupos.COMPRA_CUPOS_REUTILIZADA
                if reutilizada
                else CausaOperativaCompraCupos.COMPRA_CUPOS_CREADA
            ),
        )

    # ── Internos sync ───────────────────────────────────────────────────────

    def _obtener_inscripcion(self, inscripcion_id):
        """La inscripción, o `INSCRIPCION_NO_ENCONTRADA`."""
        inscripcion = self.inscripcion_selector.obtener_por_id(inscripcion_id)
        if inscripcion is None:
            raise InscripcionNoEncontradaError()
        return inscripcion

    def _validar_cantidad(self, cantidad: int) -> None:
        """La cantidad está dentro de los límites de dominio (`FL-04` paso 2)."""
        if cantidad < MIN_CUPOS_POR_AMPLIACION or cantidad > MAX_CUPOS_POR_AMPLIACION:
            raise CupoInvalidoError()

    def _resolver_paquete(self, inscripcion):
        """El paquete de la inscripción, vigente."""
        paquete = self.catalogo_selector.obtener_paquete(
            inscripcion.edicion_id,
            inscripcion.paquete_id,
        )
        if paquete is None or paquete.estado != EstadoPaquete.VIGENTE:
            raise PaqueteNoVigenteError()
        return paquete

    def _resolver_precio(self, paquete):
        """El precio vigente del paquete. Sin precio, no hay venta."""
        precio = self.catalogo_selector.obtener_precio_vigente(paquete.id)
        if precio is None:
            raise PaqueteNoVigenteError()
        return precio


__all__ = ["CompraCuposFlujo"]
