"""
CatalogoPresenter — transforms domain results to HTTP schemas.
"""
from modules.salesianos_fest.domain.results.catalogo_results import (
    DisciplinaResult,
    PromocionResult,
    CategoriaResult,
    PaqueteResult,
    PaqueteListResult,
)
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import (
    DisciplinaOut,
    PromocionOut,
    CategoriaOut,
    PaqueteDetailOut,
    PaqueteDisciplinaOut,
    PaqueteListOut,
    PaquetePrecioOut,
)


class CatalogoPresenter:
    """
    Transforms domain result objects to HTTP response schemas.
    Pure transformer — no DB access.
    """

    @staticmethod
    def present_disciplina(result: DisciplinaResult) -> DisciplinaOut:
        """Transform a DisciplinaResult to DisciplinaOut."""
        return DisciplinaOut(
            id=result.id,
            nombre=result.nombre,
            sigla=result.sigla,
            modalidad=result.modalidad,
            min_jugadores=result.min_jugadores,
            max_jugadores=result.max_jugadores,
        )

    @staticmethod
    def present_disciplinas(results: list[DisciplinaResult]) -> list[DisciplinaOut]:
        """Transform a list of DisciplinaResult to DisciplinaOut list."""
        return [CatalogoPresenter.present_disciplina(r) for r in results]

    @staticmethod
    def present_promocion(result: PromocionResult) -> PromocionOut:
        """Transform a PromocionResult to PromocionOut."""
        return PromocionOut(
            id=result.id,
            anio=result.anio,
            nombre=result.nombre,
        )

    @staticmethod
    def present_promociones(results: list[PromocionResult]) -> list[PromocionOut]:
        """Transform a list of PromocionResult to PromocionOut list."""
        return [CatalogoPresenter.present_promocion(r) for r in results]

    @staticmethod
    def present_categoria(result: CategoriaResult) -> CategoriaOut:
        """Transform a CategoriaResult to CategoriaOut."""
        return CategoriaOut(
            id=result.id,
            evento_id=result.evento_id,
            evento_nombre=result.evento_nombre,
            nombre=result.nombre,
            promocion_desde=result.promocion_desde,
            promocion_hasta=result.promocion_hasta,
        )

    @staticmethod
    def present_categorias(results: list[CategoriaResult]) -> list[CategoriaOut]:
        """Transform a list of CategoriaResult to CategoriaOut list."""
        return [CatalogoPresenter.present_categoria(r) for r in results]

    @staticmethod
    def present_paquete_detail(result: PaqueteResult) -> PaqueteDetailOut:
        """Transform a PaqueteResult to PaqueteDetailOut.

        Decimal prices are explicitly coerced to float so the JSON response
        emits numeric values (not strings).
        """
        return PaqueteDetailOut(
            id=result.id,
            evento_id=result.evento_id,
            nombre=result.nombre,
            descripcion=result.descripcion,
            tipo=result.tipo,
            modo_disciplinas=result.modo_disciplinas,
            cantidad_disciplinas=result.cantidad_disciplinas,
            minimo_compra_inicial=result.minimo_compra_inicial,
            precios=[
                PaquetePrecioOut(
                    etapa=p.etapa,
                    precio_unitario=float(p.precio_unitario),
                    vigente_desde=p.vigente_desde,
                    vigente_hasta=p.vigente_hasta,
                )
                for p in result.precios
            ],
            beneficios=result.beneficios,
            disciplinas=result.disciplinas,
        )

    @staticmethod
    def present_paquete_list(result: PaqueteListResult) -> PaqueteListOut:
        """Transform a PaqueteListResult to PaqueteListOut.

        Passes the canonical `disciplinas[]` (with min/max jugadores) so the
        frontend wizard never has to fetch detail after package selection.

        Also includes `beneficios[]` and `precios[]` so the quotation card
        can render full price/benefit info without a detail fetch.

        Decimal prices are explicitly coerced to float so the JSON response
        emits numeric values (not strings) — the Zod schema on the frontend
        requires `z.number()` for these fields.
        """
        return PaqueteListOut(
            id=result.id,
            evento_id=result.evento_id,
            nombre=result.nombre,
            descripcion=result.descripcion,
            tipo=result.tipo,
            modo_disciplinas=result.modo_disciplinas,
            cantidad_disciplinas=result.cantidad_disciplinas,
            cantidad_minima_compra=result.cantidad_minima_compra,
            cantidad_maxima_equipos=result.cantidad_maxima_equipos,
            precio_preventa=(
                float(result.precio_preventa) if result.precio_preventa is not None else None
            ),
            precio_regular=(
                float(result.precio_regular) if result.precio_regular is not None else None
            ),
            precio_promocional=None,  # computed from precios array; keep null at list level
            tiene_fiesta=result.tiene_fiesta,
            tiene_box=result.tiene_box,
            tiene_cerveza=result.tiene_cerveza,
            disciplinas_resumen=result.disciplinas_resumen,
            disciplinas=[
                PaqueteDisciplinaOut(
                    disciplina_id=d.disciplina_id,
                    disciplina_nombre=d.disciplina_nombre,
                    disciplina_sigla=d.disciplina_sigla,
                    min_jugadores=d.min_jugadores,
                    max_jugadores=d.max_jugadores,
                )
                for d in result.disciplinas
            ],
            beneficios=result.beneficios,
            precios=[
                PaquetePrecioOut(
                    etapa=p.etapa,
                    precio_unitario=float(p.precio_unitario),
                    vigente_desde=p.vigente_desde,
                    vigente_hasta=p.vigente_hasta,
                )
                for p in result.precios
            ],
        )

    @staticmethod
    def present_paquetes(results: list[PaqueteListResult]) -> list[PaqueteListOut]:
        """Transform a list of PaqueteListResult to PaqueteListOut list."""
        return [CatalogoPresenter.present_paquete_list(r) for r in results]
