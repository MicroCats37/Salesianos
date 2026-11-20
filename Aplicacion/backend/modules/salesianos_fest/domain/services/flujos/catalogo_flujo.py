"""`CatalogoFlujo` — el catálogo real de la edición.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

Reglas congeladas que este flujo cumple:

- **El catálogo es de UNA edición** (`RN-E01`). Nunca se resuelve "el
  catálogo" sin alcance: la edición se resuelve por el orden congelado de
  `FR-02` §2.2 y sin fallback.
- **Un módulo no habilitado no expone catálogo** (`FR-02` §2.5, `RN-E02`):
  si la edición no habilitó `inscripciones`, la respuesta es un error, no
  un catálogo vacío silencioso.
- **No hay precio de reserva** (`FL-01` paso 3): un paquete sin precio
  vigente NO aparece en el catálogo. El catálogo vacío es un hecho
  honesto; un catálogo con precios inventados es una mentira.
- **La promoción es GLOBAL** (`D-CAT-04`): el catálogo de promociones no
  cuelga de la edición. Las categorías, en cambio, sí.
- **El precio es UNITARIO** (`D-CAT-01`): el catálogo publica el precio de
  UNA persona y el mínimo COMERCIAL de participantes. La cotización deriva
  el total como `cantidad × precio_unitario` (`RN-C02`).
"""

from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.utils import timezone
from injector import inject

from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.constants import EstadoPaquete
from modules.salesianos_fest.domain.exceptions import (
    CantidadInsuficienteError,
    PaqueteNoVigenteError,
)
from modules.salesianos_fest.domain.ports import IAlcanceEdicionService
from modules.salesianos_fest.domain.results.catalogo_result import (
    BeneficioCatalogoResult,
    CatalogoCategoriasResult,
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
    CatalogoPromocionesResult,
    CategoriaCatalogoResult,
    CotizacionResult,
    DisciplinaCatalogoResult,
    PaqueteCatalogoResult,
    PrecioCatalogoResult,
    PromocionCatalogoResult,
)
from modules.salesianos_fest.domain.selectors.catalogo_selector import CatalogoSelector

#: Horas de validez de una cotización.
#:
#: Es la ventana del legacy: la cotización es un cálculo de LECTURA que
#: pertenece a la sesión del comprador, no un hecho persistido.
VIGENCIA_COTIZACION_HORAS = 24

#: Estado de una cotización recién emitida: `ACTIVA`.
ESTADO_COTIZACION_ACTIVA = "ACTIVA"


class CatalogoFlujo:
    """Lecturas del catálogo de una edición."""

    @inject
    def __init__(
        self,
        catalogo_selector: CatalogoSelector,
        alcance_edicion: IAlcanceEdicionService,
    ):
        self.catalogo_selector = catalogo_selector
        self.alcance_edicion = alcance_edicion

    async def listar_paquetes(self, edicion_id) -> CatalogoPaquetesResult:
        """Los paquetes COMPRABLES de la edición.

        Returns:
            El catálogo de paquetes con su precio vigente.
        """
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_paquetes)(edicion)

    async def listar_disciplinas(self, edicion_id) -> CatalogoDisciplinasResult:
        """Las disciplinas ACTIVAS de la edición."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_disciplinas)(edicion)

    async def listar_promociones(self, edicion_id=None) -> CatalogoPromocionesResult:
        """Las promociones ACTIVAS del catálogo GLOBAL.

        La promoción NO lleva edición (`D-CAT-04`): una cohorte de
        nacimiento es una propiedad de la persona, no de un evento. La
        EDICIÓN que scopea el catálogo va en el ENVOLTORIO, igual que en el
        catálogo de categorías.
        """
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_promociones)(edicion)

    async def listar_categorias(self, edicion_id) -> CatalogoCategoriasResult:
        """Las categorías ACTIVAS de la edición."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_categorias)(edicion)

    async def cotizar(self, paquete_id, cantidad: int) -> CotizacionResult:
        """La cotización de un paquete para una cantidad de participantes.

        Es un cálculo de LECTURA: el precio es el vigente del catálogo y el
        total lo deriva el servidor como `cantidad × precio_unitario`. El
        cliente NO envía ningún importe (`RN-C02`).

        La cantidad se contrasta contra el mínimo COMERCIAL del paquete: no
        hay un máximo global de participantes (el tope de un equipo es el de
        su disciplina, que es una regla deportiva).

        La cotización NO se persiste: devuelve además el TOKEN DE
        CONCURRENCIA (`version`) del precio, que el alta devuelve para que el
        servidor detecte que el catálogo se movió entre medias.
        """
        edicion = await sync_to_async(self._resolver_edicion)(None)
        return await sync_to_async(self._cotizar_sync)(edicion, paquete_id, cantidad)

    # ── Internos (sync) ─────────────────────────────────────────────────────

    def _resolver_edicion(self, edicion_id):
        """Resuelve la edición del alcance y exige el módulo habilitado.

        Con `edicion_id` explícito se aplica el nivel 1 del orden congelado;
        sin él, los niveles 2 → 3 → 4. En ninguno hay fallback informal.
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
        if not edicion.modulo_habilitado(ModuloLogico.INSCRIPCIONES):
            raise ModuloNoHabilitadoError()
        return edicion

    def _construir_paquetes(self, edicion) -> CatalogoPaquetesResult:
        """Proyecta los paquetes con precio vigente de la edición."""
        paquetes = []
        for paquete in self.catalogo_selector.listar_paquetes(edicion.id):
            precio = self.catalogo_selector.obtener_precio_vigente(paquete.id)
            if precio is None:
                # Sin precio vigente NO hay paquete: no se inventa un importe
                # de reserva (`FL-01` paso 3).
                continue
            paquetes.append(
                PaqueteCatalogoResult(
                    id=str(paquete.id),
                    created_at=paquete.created_at,
                    updated_at=paquete.updated_at,
                    edicion_id=str(edicion.id),
                    edicion_nombre=edicion.nombre,
                    nombre=paquete.nombre,
                    slug=paquete.slug,
                    descripcion=paquete.descripcion,
                    estado=paquete.estado,
                    tipo=paquete.tipo,
                    modo_disciplinas=paquete.modo_disciplinas,
                    cantidad_disciplinas=paquete.cantidad_disciplinas,
                    cupos_incluidos=paquete.cupos_incluidos,
                    minimo_compra_inicial=paquete.minimo_compra_inicial,
                    precio=PrecioCatalogoResult(
                        monto=precio.monto,
                        moneda=precio.moneda,
                        vigente_desde=precio.vigente_desde,
                        vigente_hasta=precio.vigente_hasta,
                    ),
                    beneficios=[
                        BeneficioCatalogoResult(
                            codigo=beneficio.codigo,
                            nombre=beneficio.nombre,
                            tipo=beneficio.tipo,
                            cantidad=beneficio.cantidad,
                        )
                        for beneficio in paquete.beneficios.all()
                    ],
                    disciplinas=[
                        CatalogoFlujo._present_disciplina(vinculo.disciplina)
                        for vinculo in paquete.disciplinas_vinculadas.all()
                    ],
                )
            )
        return CatalogoPaquetesResult(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            paquetes=paquetes,
        )

    @staticmethod
    def _present_disciplina(disciplina) -> DisciplinaCatalogoResult:
        """Proyecta una disciplina del catálogo."""
        return DisciplinaCatalogoResult(
            id=str(disciplina.id),
            created_at=disciplina.created_at,
            updated_at=disciplina.updated_at,
            edicion_id=str(disciplina.edicion_id),
            edicion_nombre=disciplina.edicion.nombre,
            nombre=disciplina.nombre,
            slug=disciplina.slug,
            estado=disciplina.estado,
            modalidad=disciplina.modalidad,
            minimo_por_equipo=disciplina.minimo_por_equipo,
            maximo_por_equipo=disciplina.maximo_por_equipo,
        )

    def _construir_disciplinas(self, edicion) -> CatalogoDisciplinasResult:
        """Proyecta las disciplinas activas de la edición."""
        disciplinas = [
            self._present_disciplina(disciplina)
            for disciplina in self.catalogo_selector.listar_disciplinas_activas(
                edicion.id
            )
        ]
        return CatalogoDisciplinasResult(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            disciplinas=disciplinas,
        )

    def _construir_promociones(self, edicion) -> CatalogoPromocionesResult:
        """Proyecta las promociones activas del catálogo global."""
        return CatalogoPromocionesResult(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            promociones=[
                PromocionCatalogoResult(
                    id=str(promocion.id),
                    created_at=promocion.created_at,
                    updated_at=promocion.updated_at,
                    anio=promocion.anio,
                    nombre=promocion.nombre,
                    estado=promocion.estado,
                )
                for promocion in self.catalogo_selector.listar_promociones()
            ],
        )

    def _construir_categorias(self, edicion) -> CatalogoCategoriasResult:
        """Proyecta las categorías activas de la edición."""
        return CatalogoCategoriasResult(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            categorias=[
                CategoriaCatalogoResult(
                    id=str(categoria.id),
                    created_at=categoria.created_at,
                    updated_at=categoria.updated_at,
                    edicion_id=str(categoria.edicion_id),
                    edicion_nombre=categoria.edicion.nombre,
                    nombre=categoria.nombre,
                    promocion_desde=categoria.promocion_desde,
                    promocion_hasta=categoria.promocion_hasta,
                    estado=categoria.estado,
                )
                for categoria in self.catalogo_selector.listar_categorias(edicion.id)
            ],
        )

    def _cotizar_sync(self, edicion, paquete_id, cantidad: int) -> CotizacionResult:
        """La cotización, contra el catálogo vigente de la edición."""
        paquete = self.catalogo_selector.obtener_paquete(edicion.id, paquete_id)
        if paquete is None or paquete.estado != EstadoPaquete.VIGENTE:
            raise PaqueteNoVigenteError()
        if cantidad < paquete.minimo_compra_inicial:
            raise CantidadInsuficienteError()

        precio = self.catalogo_selector.obtener_precio_vigente(paquete.id)
        if precio is None:
            raise PaqueteNoVigenteError()

        total = (Decimal(cantidad) * precio.monto).quantize(Decimal("0.01"))
        return CotizacionResult(
            paquete_id=str(paquete.id),
            paquete_nombre=paquete.nombre,
            minimo_cantidad=paquete.minimo_compra_inicial,
            cantidad_cotizada=cantidad,
            precio_unitario=precio.monto,
            total=total,
            moneda=precio.moneda,
            version=self.catalogo_selector.obtener_version_precio(paquete.id),
            estado=ESTADO_COTIZACION_ACTIVA,
            validez_hasta=timezone.now()
            + timedelta(hours=VIGENCIA_COTIZACION_HORAS),
        )


__all__ = ["CatalogoFlujo"]
