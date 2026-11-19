"""`InscripcionFlujo` — el alta de la inscripción inicial y su compra.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

Este flujo implementa el paso 3 de `FL-03` ("backend crea inscripción,
compra/orden pendientes") y las reglas congeladas que lo acompañan:

**RN-C01 — Cada dominio tiene su propio flujo de compra.** La compra la crea
el dominio de inscripción, NO un carrito conjunto, y la crea a través de la
interfaz CONGELADA de `commerce` (`CompraFlujo`).

**RN-C02 — El servidor congela el precio.** El total lo deriva `commerce` de
las líneas del snapshot; este flujo entrega el precio VIGENTE del catálogo y
NO acepta ningún importe del cliente.

**RN-I02 — Una compra pendiente NO habilita cupos.** La inscripción nace con
`cupos_pagados = 0`. La activación de derechos (que sí incrementa los cupos)
es de `DOM-02`, a través del puerto `IActivadorDominioCompra` de FND-05.

**RN-I01 — La inscripción tiene un responsable.** El responsable sale de la
cuenta autenticada; el cliente no declara quién es.

**Idempotencia del alta.** Un reintento NO crea una segunda inscripción ni
una segunda compra: la restricción única de la base de datos y la
referencia estable de la inscripción lo garantizan.

**Recuperabilidad.** La inscripción y su compra son hechos SEPARADOS: si la
compra falla, la inscripción queda viva y el reintento la reutiliza y crea
(o recupera) su compra. Perder una inscripción ya creada sería peor que
reintentarla.
"""

import asyncio
import uuid

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.schemas.compra_schemas import (
    CompraCreateData,
    LineaCompraSnapshot,
)
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo
from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.constants import (
    CausaOperativaInscripcion,
    EstadoPaquete,
)
from modules.salesianos_fest.domain.exceptions import (
    DisciplinaNoPermitidaError,
    EquipoDuplicadoError,
    InscripcionNoEncontradaError,
    PaqueteNoVigenteError,
)
from modules.salesianos_fest.domain.ports import IAlcanceEdicionService
from modules.salesianos_fest.domain.referencia import referencia_inicial
from modules.salesianos_fest.domain.results.inscripcion_result import (
    CompraInscripcionResult,
    EquipoResult,
    InscripcionDetalleResult,
    InscripcionInicialResult,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.selectors.catalogo_selector import CatalogoSelector
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.services.core.catalogo_core_service import (
    CatalogoCoreService,
)
from modules.salesianos_fest.domain.services.core.inscripcion_core_service import (
    InscripcionCoreService,
)

#: Cuántas veces reintenta el flujo la lectura de la inscripción ganadora
#: cuando dos altas compiten por la misma fila.
REINTENTOS_INSCRIPCION = 5

#: Espera entre reintentos, en segundos.
ESPERA_REINTENTO_INSCRIPCION_SEGUNDOS = 0.05


class InscripcionFlujo:
    """Casos de uso de escritura sobre las inscripciones."""

    @inject
    def __init__(
        self,
        catalogo_selector: CatalogoSelector,
        inscripcion_selector: InscripcionSelector,
        catalogo_core: CatalogoCoreService,
        inscripcion_core: InscripcionCoreService,
        alcance_edicion: IAlcanceEdicionService,
        compra_flujo: CompraFlujo,
    ):
        self.catalogo_selector = catalogo_selector
        self.inscripcion_selector = inscripcion_selector
        self.catalogo_core = catalogo_core
        self.inscripcion_core = inscripcion_core
        self.alcance_edicion = alcance_edicion
        self.compra_flujo = compra_flujo

    async def crear_inscripcion_inicial(
        self,
        data: InscripcionInicialData,
    ) -> InscripcionInicialResult:
        """Crea (o reutiliza) la inscripción inicial y su compra pendiente.

        Returns:
            El detalle de la inscripción, su compra y la causa operativa.
        """
        edicion = await sync_to_async(self._resolver_edicion)(data.edicion_id)
        paquete = await sync_to_async(self._resolver_paquete)(edicion, data.paquete_id)
        precio = await sync_to_async(self._resolver_precio)(paquete)
        await sync_to_async(self._validar_equipos)(paquete, data.equipos)

        inscripcion, reutilizada = await self._obtener_o_crear_inscripcion(
            edicion,
            paquete,
            data,
        )
        compra, compra_reutilizada = await self._crear_compra(
            inscripcion,
            paquete,
            precio,
            data.responsable_id,
        )
        detalle = await sync_to_async(self._construir_detalle)(inscripcion)

        return InscripcionInicialResult(
            inscripcion=detalle,
            compra=CompraInscripcionResult(
                compra_id=str(compra.id),
                orden_pago_id=str(compra.orden_pago_id),
                estado=compra.estado,
                total=compra.total,
                moneda=compra.moneda,
                reutilizada=compra_reutilizada,
            ),
            causa_operativa=(
                CausaOperativaInscripcion.INSCRIPCION_REUTILIZADA
                if reutilizada
                else CausaOperativaInscripcion.INSCRIPCION_CREADA
            ),
        )

    async def obtener_inscripcion(self, inscripcion_id) -> InscripcionDetalleResult:
        """El detalle de una inscripción y su saldo de cupos."""
        inscripcion = await sync_to_async(self.inscripcion_selector.obtener_por_id)(
            inscripcion_id
        )
        if inscripcion is None:
            raise InscripcionNoEncontradaError()
        return await sync_to_async(self._construir_detalle)(inscripcion)

    # ── Internos sync ───────────────────────────────────────────────────────

    def _resolver_edicion(self, edicion_id):
        """Resuelve la edición del alcance y exige el módulo habilitado."""
        edicion = self.alcance_edicion.resolver_explicita(
            edicion_id,
            exigir_publicada=True,
        )
        if not edicion.modulo_habilitado(ModuloLogico.INSCRIPCIONES):
            raise ModuloNoHabilitadoError()
        return edicion

    def _resolver_paquete(self, edicion, paquete_id):
        """El paquete dentro de la edición, vigente y con precio vigente."""
        paquete = self.catalogo_selector.obtener_paquete(edicion.id, paquete_id)
        if paquete is None or paquete.estado != EstadoPaquete.VIGENTE:
            raise PaqueteNoVigenteError()
        return paquete

    def _resolver_precio(self, paquete):
        """El precio vigente del paquete. Sin precio, no hay venta."""
        precio = self.catalogo_selector.obtener_precio_vigente(paquete.id)
        if precio is None:
            raise PaqueteNoVigenteError()
        return precio

    def _validar_equipos(self, paquete, equipos):
        """Comprueba que las disciplinas declaradas estén permitidas.

        El padrón NO lo elige el cliente: cada disciplina debe existir en la
        edición, estar `ACTIVA` y formar parte del paquete.
        """
        vistas = set()
        for equipo in equipos:
            disciplina = self.catalogo_core.disciplina_permitida(
                paquete,
                equipo.disciplina_id,
            )
            if disciplina is None:
                raise DisciplinaNoPermitidaError()
            if str(disciplina.id) in vistas:
                raise EquipoDuplicadoError()
            vistas.add(str(disciplina.id))

    async def _obtener_o_crear_inscripcion(self, edicion, paquete, data):
        """Devuelve `(inscripcion, reutilizada)`.

        La garantía de NO duplicar la inscripción la da la base de datos: la
        restricción única condicional `(edición, responsable, paquete)`. Si
        dos altas simultáneas compiten, la que pierde la carrera reutiliza
        la que ganó.
        """
        try:
            inscripcion, reutilizada = await sync_to_async(
                self._crear_o_reutilizar_sync
            )(
                edicion,
                paquete,
                data,
            )
        except IntegrityError:
            # La restricción única rechazó la segunda inscripción: la que
            # ganó la carrera es la buena y se reutiliza.
            existente = await self._esperar_inscripcion_ganadora(
                edicion,
                paquete,
                data,
            )
            if existente is None:
                raise
            return existente, True

        return inscripcion, reutilizada

    async def _esperar_inscripcion_ganadora(self, edicion, paquete, data):
        """Espera a que la fila ganadora sea visible y la devuelve.

        Cuando dos altas compiten, la perdedora recibe un `IntegrityError`
        en cuanto la ganadora COMMITEA. Puede haber un instante en el que
        la perdedora aún no la ve: se reintenta un número acotado de veces
        antes de propagar el error.
        """
        for intento in range(REINTENTOS_INSCRIPCION):
            existente = await sync_to_async(
                self.inscripcion_selector.obtener_por_responsable_y_paquete
            )(edicion.id, data.responsable_id, paquete.id)
            if existente is not None:
                return existente
            await asyncio.sleep(ESPERA_REINTENTO_INSCRIPCION_SEGUNDOS)
        return None

    @transaction.atomic()
    def _crear_o_reutilizar_sync(self, edicion, paquete, data):
        """Alta atómica de la inscripción y sus equipos.

        Returns:
            La tupla `(inscripcion, reutilizada)`.
        """
        existente = self.inscripcion_selector.obtener_por_responsable_y_paquete(
            edicion.id,
            data.responsable_id,
            paquete.id,
        )
        if existente is not None:
            return existente, True

        inscripcion = self.inscripcion_core.crear(
            edicion_id=edicion.id,
            responsable_id=data.responsable_id,
            paquete_id=paquete.id,
            referencia=f"INS-{uuid.uuid4().hex[:12].upper()}",
            cupos_solicitados=paquete.cupos_incluidos,
        )
        self.inscripcion_core.crear_equipos(inscripcion, data.equipos)
        return inscripcion, False

    async def _crear_compra(self, inscripcion, paquete, precio, responsable_id):
        """Crea (o reutiliza) la compra pendiente de la inscripción.

        La compra la crea `commerce` a través de su interfaz CONGELADA: este
        flujo sólo entrega el snapshot ya resuelto por el servidor.
        """
        intencion = CompraCreateData(
            persona_id=responsable_id,
            origen=OrigenCompra.INSCRIPCION,
            lineas=[
                LineaCompraSnapshot(
                    concepto_tipo="PAQUETE",
                    concepto_id=str(paquete.id),
                    concepto_nombre=paquete.nombre,
                    cantidad=paquete.cupos_incluidos,
                    precio_unitario=precio.monto,
                    precio_aplicado=precio.monto,
                )
            ],
            referencia=self._referencia_compra(inscripcion),
            moneda=precio.moneda,
        )
        return await self.compra_flujo.crear_o_reutilizar_compra(intencion)

    @staticmethod
    def _referencia_compra(inscripcion) -> str:
        """La referencia de la INTENCIÓN de compra de la inscripción.

        Es estable: un reintento del alta abre la MISMA compra pendiente en
        vez de crear otra (`FR-04` I-4). El FORMATO lo declara
        `domain/referencia.py`, que es el mismo que lee el activador de
        derechos (`DOM-02`).
        """
        return referencia_inicial(inscripcion.id)

    def _construir_detalle(self, inscripcion) -> InscripcionDetalleResult:
        """Proyecta la inscripción con su saldo de cupos."""
        equipos = list(self.inscripcion_selector.listar_equipos(inscripcion.id))
        return InscripcionDetalleResult(
            id=str(inscripcion.id),
            created_at=inscripcion.created_at,
            updated_at=inscripcion.updated_at,
            edicion_id=str(inscripcion.edicion_id),
            edicion_nombre=inscripcion.edicion.nombre,
            responsable_id=str(inscripcion.responsable_id),
            paquete_id=str(inscripcion.paquete_id),
            paquete_nombre=inscripcion.paquete.nombre,
            estado=inscripcion.estado,
            referencia=inscripcion.referencia,
            cupos_solicitados=inscripcion.cupos_solicitados,
            cupos_pagados=inscripcion.cupos_pagados,
            cupos_asignados=inscripcion.cupos_asignados,
            # El saldo lo calcula el servidor (`RN-I03`): nunca es negativo.
            cupos_disponibles=max(
                inscripcion.cupos_pagados - inscripcion.cupos_asignados,
                0,
            ),
            equipos=[
                EquipoResult(
                    id=str(equipo.id),
                    created_at=equipo.created_at,
                    updated_at=equipo.updated_at,
                    disciplina_id=str(equipo.disciplina_id),
                    disciplina_nombre=equipo.disciplina.nombre,
                    nombre=equipo.nombre,
                    estado=equipo.estado,
                )
                for equipo in equipos
            ],
        )


__all__ = ["InscripcionFlujo"]
