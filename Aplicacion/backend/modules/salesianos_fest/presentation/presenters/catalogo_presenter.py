"""`CatalogoPresenter` — results del catálogo → wrappers HTTP.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter) ·
          `contract/PLAN_REFACTORIZACION.md` §3.A

El presenter es un TRANSFORMADOR PURO: recibe un result object y devuelve un
schema HTTP. No consulta la base de datos, no llama a selectores y no
construye mensajes públicos de error.

Reglas:
- un método público por endpoint (`present_paquetes`, `present_disciplinas`);
- sólo `@staticmethod`;
- nada de `z.any()` ni campos genéricos: cada wrapper es tipado.
"""

from uuid import UUID

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
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import (
    BeneficioOut,
    CatalogoCategoriasOut,
    CatalogoDisciplinasOut,
    CatalogoPaquetesOut,
    CatalogoPromocionesOut,
    CategoriaOut,
    CotizacionOut,
    DisciplinaOut,
    PaqueteOut,
    PrecioOut,
    PromocionOut,
)


class CatalogoPresenter:
    """Transformador del catálogo de inscripción."""

    @staticmethod
    def present_paquetes(result: CatalogoPaquetesResult) -> CatalogoPaquetesOut:
        """Proyecta el catálogo de paquetes al wrapper HTTP."""
        return CatalogoPaquetesOut(
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            paquetes=[
                CatalogoPresenter._present_paquete(paquete)
                for paquete in result.paquetes
            ],
        )

    @staticmethod
    def present_disciplinas(
        result: CatalogoDisciplinasResult,
    ) -> CatalogoDisciplinasOut:
        """Proyecta el catálogo de disciplinas al wrapper HTTP."""
        return CatalogoDisciplinasOut(
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            disciplinas=[
                CatalogoPresenter._present_disciplina(disciplina)
                for disciplina in result.disciplinas
            ],
        )

    @staticmethod
    def present_promociones(
        result: CatalogoPromocionesResult,
    ) -> CatalogoPromocionesOut:
        """Proyecta el catálogo global de promociones del alcance."""
        return CatalogoPromocionesOut(
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            promociones=[
                CatalogoPresenter._present_promocion(promocion)
                for promocion in result.promociones
            ],
        )

    @staticmethod
    def present_categorias(
        result: CatalogoCategoriasResult,
    ) -> CatalogoCategoriasOut:
        """Proyecta el catálogo de categorías de la edición."""
        return CatalogoCategoriasOut(
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            categorias=[
                CatalogoPresenter._present_categoria(categoria)
                for categoria in result.categorias
            ],
        )

    @staticmethod
    def present_cotizacion(result: CotizacionResult) -> CotizacionOut:
        """Proyecta la cotización de un paquete."""
        return CotizacionOut(
            paquete_id=UUID(result.paquete_id),
            paquete_nombre=result.paquete_nombre,
            minimo_cantidad=result.minimo_cantidad,
            cantidad_cotizada=result.cantidad_cotizada,
            precio_unitario=result.precio_unitario,
            total=result.total,
            moneda=result.moneda,
            version=result.version,
            estado=result.estado,
            validez_hasta=result.validez_hasta,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    @staticmethod
    def _present_paquete(paquete: PaqueteCatalogoResult) -> PaqueteOut:
        """Proyecta un paquete y sus bloques."""
        return PaqueteOut(
            id=UUID(paquete.id),
            created_at=paquete.created_at,
            updated_at=paquete.updated_at,
            edicion_id=UUID(paquete.edicion_id),
            edicion_nombre=paquete.edicion_nombre,
            nombre=paquete.nombre,
            slug=paquete.slug,
            descripcion=paquete.descripcion,
            estado=paquete.estado,
            tipo=paquete.tipo,
            modo_disciplinas=paquete.modo_disciplinas,
            cantidad_disciplinas=paquete.cantidad_disciplinas,
            cupos_incluidos=paquete.cupos_incluidos,
            minimo_compra_inicial=paquete.minimo_compra_inicial,
            precio=CatalogoPresenter._present_precio(paquete.precio),
            beneficios=[
                CatalogoPresenter._present_beneficio(beneficio)
                for beneficio in paquete.beneficios
            ],
            disciplinas=[
                CatalogoPresenter._present_disciplina(disciplina)
                for disciplina in paquete.disciplinas
            ],
        )

    @staticmethod
    def _present_promocion(promocion: PromocionCatalogoResult) -> PromocionOut:
        """Proyecta una promoción del catálogo global."""
        return PromocionOut(
            id=UUID(promocion.id),
            created_at=promocion.created_at,
            updated_at=promocion.updated_at,
            anio=promocion.anio,
            nombre=promocion.nombre,
            estado=promocion.estado,
        )

    @staticmethod
    def _present_categoria(categoria: CategoriaCatalogoResult) -> CategoriaOut:
        """Proyecta una categoría de la edición."""
        return CategoriaOut(
            id=UUID(categoria.id),
            created_at=categoria.created_at,
            updated_at=categoria.updated_at,
            edicion_id=UUID(categoria.edicion_id),
            edicion_nombre=categoria.edicion_nombre,
            nombre=categoria.nombre,
            promocion_desde=categoria.promocion_desde,
            promocion_hasta=categoria.promocion_hasta,
            estado=categoria.estado,
        )

    @staticmethod
    def _present_precio(precio: PrecioCatalogoResult) -> PrecioOut:
        """Proyecta el precio vigente del catálogo."""
        return PrecioOut(
            monto=precio.monto,
            moneda=precio.moneda,
            vigente_desde=precio.vigente_desde,
            vigente_hasta=precio.vigente_hasta,
        )

    @staticmethod
    def _present_beneficio(beneficio: BeneficioCatalogoResult) -> BeneficioOut:
        """Proyecta un beneficio ofrecido."""
        return BeneficioOut(
            codigo=beneficio.codigo,
            nombre=beneficio.nombre,
            tipo=beneficio.tipo,
            cantidad=beneficio.cantidad,
        )

    @staticmethod
    def _present_disciplina(disciplina: DisciplinaCatalogoResult) -> DisciplinaOut:
        """Proyecta una disciplina."""
        return DisciplinaOut(
            id=UUID(disciplina.id),
            created_at=disciplina.created_at,
            updated_at=disciplina.updated_at,
            edicion_id=UUID(disciplina.edicion_id),
            edicion_nombre=disciplina.edicion_nombre,
            nombre=disciplina.nombre,
            slug=disciplina.slug,
            estado=disciplina.estado,
            modalidad=disciplina.modalidad,
            minimo_por_equipo=disciplina.minimo_por_equipo,
            maximo_por_equipo=disciplina.maximo_por_equipo,
        )


__all__ = ["CatalogoPresenter"]
