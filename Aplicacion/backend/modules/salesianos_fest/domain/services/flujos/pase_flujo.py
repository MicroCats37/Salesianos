"""`PaseFlujo` — el catálogo de pases y la lectura de los lotes comprados.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC.

Reglas congeladas que este flujo cumple:

- **El catálogo es de UNA edición** (`RN-E01`). Nunca se resuelve "el
  catálogo" sin alcance: la edición se resuelve por el orden congelado de
  `FR-02` §2.2 y sin fallback.
- **Un módulo no habilitado no expone catálogo** (`FR-02` §2.5, `RN-E02`):
  si la edición no habilitó `pases`, la respuesta es un error, no un
  catálogo vacío silencioso.
- **No hay precio de reserva**: un pase sin precio vigente NO aparece en el
  catálogo. El catálogo vacío es un hecho honesto; un catálogo con precios
  inventados es una mentira.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.exceptions import PaseNoEncontradoError
from modules.salesianos_fest.domain.ports import IAlcanceEdicionService
from modules.salesianos_fest.domain.results.pase_result import (
    AdminPaseListItemResult,
    AdminPaseListaResult,
    PaseCatalogoListaResult,
    PaseCatalogoResult,
    PaseDetalleResult,
    PrecioPaseResult,
)
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector


class PaseFlujo:
    """Lecturas del catálogo de pases y de los lotes comprados."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        alcance_edicion: IAlcanceEdicionService,
    ):
        self.pase_selector = pase_selector
        self.alcance_edicion = alcance_edicion

    async def listar_pases(self, edicion_id) -> PaseCatalogoListaResult:
        """Los pases COMPRABLES de la edición."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_pases)(edicion)

    async def obtener_pase(self, edicion_id, pase_id) -> PaseDetalleResult:
        """El detalle de un pase de la edición."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
        return await sync_to_async(self._construir_pase)(edicion, pase_id)

    async def listar_compras(
        self,
        edicion_id=None,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AdminPaseListaResult:
        """El listado administrativo de lotes de pases."""
        return await sync_to_async(self._construir_compras)(
            edicion_id,
            estado,
            page,
            page_size,
        )

    # ── Internos (sync) ─────────────────────────────────────────────────────

    def _resolver_edicion(self, edicion_id):
        """Resuelve la edición del alcance y exige el módulo `pases`."""
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

    def _construir_pases(self, edicion) -> PaseCatalogoListaResult:
        """Proyecta los pases con precio vigente de la edición."""
        pases = []
        for pase in self.pase_selector.listar_pases(edicion.id):
            precio = self.pase_selector.obtener_precio_vigente(pase.id)
            if precio is None:
                # Sin precio vigente NO hay pase: no se inventa un importe de
                # reserva.
                continue
            pases.append(
                PaseCatalogoResult(
                    id=str(pase.id),
                    created_at=pase.created_at,
                    updated_at=pase.updated_at,
                    edicion_id=str(edicion.id),
                    edicion_nombre=edicion.nombre,
                    nombre=pase.nombre,
                    slug=pase.slug,
                    descripcion=pase.descripcion,
                    estado=pase.estado,
                    precio=self._proyectar_precio(precio),
                )
            )
        return PaseCatalogoListaResult(
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            pases=pases,
        )

    def _construir_pase(self, edicion, pase_id) -> PaseDetalleResult:
        """Proyecta el detalle de un pase.

        Un pase RETIRADO sí se puede consultar por su identificador: el
        catálogo histórico se conserva. Lo que no existe NO se inventa.
        """
        pase = self.pase_selector.obtener_pase(edicion.id, pase_id)
        if pase is None:
            raise PaseNoEncontradoError()
        precio = self.pase_selector.obtener_precio_vigente(pase.id)
        return PaseDetalleResult(
            id=str(pase.id),
            created_at=pase.created_at,
            updated_at=pase.updated_at,
            edicion_id=str(edicion.id),
            edicion_nombre=edicion.nombre,
            nombre=pase.nombre,
            slug=pase.slug,
            descripcion=pase.descripcion,
            estado=pase.estado,
            # Sin precio vigente el precio es `None`: NO se inventa un
            # importe de reserva (`FL-01` paso 3).
            precio=self._proyectar_precio(precio) if precio is not None else None,
        )

    @staticmethod
    def _proyectar_precio(precio) -> PrecioPaseResult:
        """Proyecta el precio vigente."""
        return PrecioPaseResult(
            monto=precio.monto,
            moneda=precio.moneda,
            vigente_desde=precio.vigente_desde,
            vigente_hasta=precio.vigente_hasta,
        )

    def _construir_compras(
        self,
        edicion_id,
        estado,
        page: int,
        page_size: int,
    ) -> AdminPaseListaResult:
        """Proyecta el listado administrativo de lotes."""
        page = max(1, int(page or 1))
        page_size = max(1, min(int(page_size or 25), 100))
        total = self.pase_selector.contar_compras_pase(edicion_id, estado)
        offset = (page - 1) * page_size
        lotes = list(
            self.pase_selector.listar_compras_pase(edicion_id, estado)[
                offset : offset + page_size
            ]
        )
        return AdminPaseListaResult(
            items=[
                AdminPaseListItemResult(
                    compra_pase_id=str(lote.id),
                    estado=lote.estado,
                    pase_id=str(lote.pase_id),
                    pase_nombre=lote.pase.nombre,
                    edicion_id=str(lote.edicion_id),
                    edicion_nombre=lote.edicion.nombre,
                    comprador_persona_id=str(lote.comprador_id),
                    comprador_nombres=lote.comprador.nombres,
                    cantidad=lote.cantidad,
                    asignados=lote.asignados,
                    total=lote.total,
                    moneda=lote.moneda,
                    creado_en=lote.created_at,
                )
                for lote in lotes
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if total else 0,
        )


__all__ = ["PaseFlujo"]
