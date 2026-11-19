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
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
    DisciplinaCatalogoResult,
    PaqueteCatalogoResult,
    PrecioCatalogoResult,
)
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import (
    BeneficioOut,
    CatalogoDisciplinasOut,
    CatalogoPaquetesOut,
    DisciplinaOut,
    PaqueteOut,
    PrecioOut,
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
            cupos_incluidos=paquete.cupos_incluidos,
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
