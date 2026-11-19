"""`CatalogoFlujo` — el catálogo real de la edición.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

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
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.eventos.domain.constants import ModuloLogico
from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.exceptions import PaqueteNoVigenteError
from modules.salesianos_fest.domain.ports import IAlcanceEdicionService
from modules.salesianos_fest.domain.results.catalogo_result import (
    BeneficioCatalogoResult,
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
    DisciplinaCatalogoResult,
    PaqueteCatalogoResult,
    PrecioCatalogoResult,
)
from modules.salesianos_fest.domain.selectors.catalogo_selector import CatalogoSelector


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
                    cupos_incluidos=paquete.cupos_incluidos,
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


__all__ = ["CatalogoFlujo"]
