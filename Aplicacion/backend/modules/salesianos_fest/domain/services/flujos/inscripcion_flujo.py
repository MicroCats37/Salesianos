"""`InscripcionFlujo` — el alta de la inscripción inicial y su compra.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

Este flujo implementa el paso 3 de `FL-03` ("backend crea inscripción,
compra/orden pendientes") y las reglas congeladas que lo acompañan:

**RN-C01 — Cada dominio tiene su propio flujo de compra.** La compra la crea
el dominio de inscripción, NO un carrito conjunto, y la crea a través de la
interfaz CONGELADA de `commerce` (`CompraFlujo`).

**RN-C02 — El servidor congela el precio.** El total lo deriva `commerce` de
las líneas del snapshot; este flujo entrega el precio VIGENTE del catálogo y
NO acepta ningún importe del cliente.

**D-CAT-01 — El precio es POR PERSONA.** El cliente declara la CANTIDAD de
participantes (mínimo comercial: `Paquete.minimo_compra_inicial`); el
servidor entrega el precio UNITARIO vigente y el total lo deriva `commerce`
como `cantidad × precio_unitario`. NO hay un máximo global de participantes:
el tope de un equipo es el de su disciplina, que es una regla deportiva.

**D-CAT-01/D-CAT-05 — La categoría la DERIVA el servidor.** La promoción
principal se proyecta contra el rango de las categorías de la edición y de
ahí sale la categoría de TODOS los equipos de la inscripción. El cliente
declara la promoción; nunca la categoría.

**D-CAT-02 — La fusión es DESCRIPTIVA.** `fusion_promocion` nombra la segunda
cohorte de una promoción fusionada. NO altera cupos, pago, categoría,
elegibilidad de equipo ni cuadro competitivo.

**RN-I02 — Una compra pendiente NO habilita cupos.** La inscripción nace con
`cupos_pagados = 0`. La activación de derechos (que sí incrementa los cupos)
es de `DOM-02`, a través del puerto `IActivadorDominioCompra` de FND-05. La
activación concede EXACTAMENTE los `cantidad` cupos que congeló el snapshot.

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
from decimal import Decimal

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
    CONCEPTO_LINEA_PAQUETE,
    CausaOperativaInscripcion,
    EstadoPaquete,
    EstadoPromocion,
    ModoDisciplinas,
)
from modules.salesianos_fest.domain.exceptions import (
    CantidadInsuficienteError,
    CategoriaNoResueltaError,
    DisciplinaNoPermitidaError,
    EquipoDuplicadoError,
    EquiposFueraDePaqueteError,
    FusionPromocionInvalidaError,
    InscripcionNoEncontradaError,
    PaqueteNoVigenteError,
    PrecioCambiadoError,
    PromocionNoEncontradaError,
)
from modules.salesianos_fest.domain.ports import IAlcanceEdicionService
from modules.salesianos_fest.domain.referencia import referencia_inicial
from modules.salesianos_fest.domain.results.inscripcion_result import (
    CompraInscripcionResult,
    EquipoResult,
    InscripcionDetalleResult,
    InscripcionInicialResult,
    PromocionResult,
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
        cantidad = await sync_to_async(self._validar_cantidad)(paquete, data.cantidad)
        await sync_to_async(self._validar_version_cotizacion)(
            paquete,
            data.cotizacion_version,
        )
        promocion = await sync_to_async(self._resolver_promocion)(data.promocion_id)
        fusion = await sync_to_async(self._resolver_fusion)(
            data.fusion_promocion_id,
            promocion,
        )
        categoria = await sync_to_async(self._resolver_categoria)(edicion, promocion)
        await sync_to_async(self._validar_equipos)(paquete, data.equipos)

        inscripcion, reutilizada = await self._obtener_o_crear_inscripcion(
            edicion,
            paquete,
            data,
            cantidad,
            promocion,
            fusion,
            categoria,
        )
        compra, compra_reutilizada = await self._crear_compra(
            inscripcion,
            paquete,
            precio,
            cantidad,
            data.responsable_id,
        )
        detalle = await sync_to_async(self._construir_detalle)(inscripcion)

        return InscripcionInicialResult(
            inscripcion=detalle,
            compra=self._presentar_compra(compra, compra_reutilizada, cantidad),
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
        """El precio vigente del paquete. Sin precio, no hay venta.

        El precio es UNITARIO: es el precio de UNA persona (`D-CAT-01`).
        """
        precio = self.catalogo_selector.obtener_precio_vigente(paquete.id)
        if precio is None:
            raise PaqueteNoVigenteError()
        return precio

    def _validar_cantidad(self, paquete, cantidad: int) -> int:
        """La cantidad de participantes contra el mínimo COMERCIAL del paquete.

        El mínimo es del PAQUETE (`Paquete.minimo_compra_inicial`), no un
        máximo global: el tope de un equipo es el de su disciplina, que es
        una regla deportiva (`D-CAT-01`).
        """
        if cantidad < paquete.minimo_compra_inicial:
            raise CantidadInsuficienteError()
        return cantidad

    def _validar_version_cotizacion(self, paquete, cotizacion_version) -> None:
        """Comprueba el TOKEN DE CONCURRENCIA de la cotización, si viaja.

        El token es la versión del precio que el comprador vio. Si el
        catálogo ya no está en esa versión, el alta se rechaza: es mejor
        obligar a cotizar de nuevo que cobrar una cantidad que nadie vió
        (`RN-C02`).

        Sin token NO hay comprobación: el precio vigente es el que rige.
        """
        if cotizacion_version is None:
            return
        vigente = self.catalogo_selector.obtener_version_precio(paquete.id)
        if cotizacion_version != vigente:
            raise PrecioCambiadoError()

    def _resolver_promocion(self, promocion_id):
        """La promoción (cohorte) que compra. GLOBAL y ACTIVA.

        La promoción es la que DECLARA el cliente; el servidor la contrasta
        contra el catálogo global.
        """
        promocion = self.catalogo_selector.obtener_promocion(promocion_id)
        if promocion is None or promocion.estado != EstadoPromocion.ACTIVA:
            raise PromocionNoEncontradaError()
        return promocion

    def _resolver_fusion(self, fusion_promocion_id, promocion):
        """La promoción fusionada: OPCIONAL, DESCRIPTIVA y DISTINTA.

        La fusión nombra la segunda cohorte de una promoción fusionada. NO
        altera cupos, pago, categoría, elegibilidad ni cuadro competitivo
        (`D-CAT-02`): por eso su única regla es que no sea la misma que la
        promoción principal.
        """
        if fusion_promocion_id is None:
            return None

        fusion = self.catalogo_selector.obtener_promocion(fusion_promocion_id)
        if fusion is None or fusion.estado != EstadoPromocion.ACTIVA:
            raise PromocionNoEncontradaError()
        if fusion.id == promocion.id:
            raise FusionPromocionInvalidaError()
        return fusion

    def _resolver_categoria(self, edicion, promocion):
        """La categoría DERIVADA de la promoción principal.

        Es el ÚNICO punto de derivación (`D-CAT-05`): el cliente declara la
        promoción, nunca la categoría. Si la cohorte no cae en ninguna
        categoría activa de la edición, la inscripción NO tiene banda con la
        que competir y se rechaza: no se inventa ninguna.
        """
        categoria = self.catalogo_selector.obtener_categoria_por_promocion(
            edicion.id,
            promocion.anio,
        )
        if categoria is None:
            raise CategoriaNoResueltaError()
        return categoria

    def _validar_equipos(self, paquete, equipos):
        """Comprueba que las disciplinas declaradas estén permitidas.

        El padrón NO lo elige el cliente: cada disciplina debe existir en la
        edición, estar `ACTIVA` y formar parte del paquete.

        Además, la CANTIDAD y el CONJUNTO de equipos los manda el PAQUETE:

        - `modo_disciplinas = FIJO` — hay que declarar EXACTAMENTE las
          disciplinas vinculadas al paquete.
        - `modo_disciplinas = ELEGIBLE` — hay que declarar hasta
          `cantidad_disciplinas` de las disciplinas vinculadas al paquete.
        """
        vistas = set()
        permitidas = set()
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
            permitidas.add(str(disciplina.id))

        vinculadas = {
            str(vinculo.disciplina_id)
            for vinculo in paquete.disciplinas_vinculadas.all()
        }
        if not permitidas.issubset(vinculadas):
            raise DisciplinaNoPermitidaError()

        if paquete.modo_disciplinas == ModoDisciplinas.FIJO:
            if permitidas != vinculadas:
                raise EquiposFueraDePaqueteError()
            return

        if len(permitidas) > paquete.cantidad_disciplinas:
            raise EquiposFueraDePaqueteError()

    async def _obtener_o_crear_inscripcion(
        self,
        edicion,
        paquete,
        data,
        cantidad,
        promocion,
        fusion,
        categoria,
    ):
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
                cantidad,
                promocion,
                fusion,
                categoria,
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
    def _crear_o_reutilizar_sync(
        self,
        edicion,
        paquete,
        data,
        cantidad,
        promocion,
        fusion,
        categoria,
    ):
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
            promocion_id=promocion.id,
            fusion_promocion_id=fusion.id if fusion is not None else None,
            referencia=f"INS-{uuid.uuid4().hex[:12].upper()}",
            cupos_solicitados=cantidad,
        )
        self.inscripcion_core.crear_equipos(
            inscripcion,
            data.equipos,
            categoria,
        )
        return inscripcion, False

    async def _crear_compra(self, inscripcion, paquete, precio, cantidad, responsable_id):
        """Crea (o reutiliza) la compra pendiente de la inscripción.

        La compra la crea `commerce` a través de su interfaz CONGELADA: este
        flujo sólo entrega el snapshot ya resuelto por el servidor.

        La línea congela la CANTIDAD de participantes y el PRECIO UNITARIO
        vigente: el total lo deriva `commerce` como
        `cantidad × precio_unitario` (`RN-C02`). La activación de derechos
        concederá EXACTAMENTE esos `cantidad` cupos (`RN-I02`).
        """
        intencion = CompraCreateData(
            persona_id=responsable_id,
            origen=OrigenCompra.INSCRIPCION,
            lineas=[
                LineaCompraSnapshot(
                    concepto_tipo="PAQUETE",
                    concepto_id=str(paquete.id),
                    concepto_nombre=paquete.nombre,
                    cantidad=cantidad,
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
            promocion=PromocionResult(
                id=str(inscripcion.promocion_id),
                anio=inscripcion.promocion.anio,
                nombre=inscripcion.promocion.nombre,
            ),
            fusion_promocion=(
                PromocionResult(
                    id=str(inscripcion.fusion_promocion_id),
                    anio=inscripcion.fusion_promocion.anio,
                    nombre=inscripcion.fusion_promocion.nombre,
                )
                if inscripcion.fusion_promocion_id is not None
                else None
            ),
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
                    categoria_id=str(equipo.categoria_id),
                    categoria_nombre=equipo.categoria.nombre,
                    nombre=equipo.nombre,
                    estado=equipo.estado,
                )
                for equipo in equipos
            ],
        )

    @staticmethod
    def _presentar_compra(
        compra,
        reutilizada: bool,
        cantidad: int,
    ) -> CompraInscripcionResult:
        """Proyecta la compra con los hechos CONGELADOS en su snapshot.

        Los valores salen del snapshot, no del catálogo vigente: una compra
        reutilizada conserva su precio y su cantidad originales aunque el
        catálogo haya cambiado después (`RN-M03`).
        """
        cantidad_congelada = cantidad
        precio_unitario = Decimal("0.00")
        for linea in compra.lineas_snapshot or []:
            if not isinstance(linea, dict):
                continue
            if linea.get("concepto_tipo") != CONCEPTO_LINEA_PAQUETE:
                continue
            cantidad_congelada = int(linea.get("cantidad") or cantidad_congelada)
            precio_unitario = Decimal(
                str(linea.get("precio_aplicado") or linea.get("precio_unitario") or 0)
            )
            break

        return CompraInscripcionResult(
            compra_id=str(compra.id),
            orden_pago_id=str(compra.orden_pago_id),
            estado=compra.estado,
            cantidad=cantidad_congelada,
            precio_unitario=precio_unitario,
            total=compra.total,
            moneda=compra.moneda,
            reutilizada=reutilizada,
        )


__all__ = ["InscripcionFlujo"]
