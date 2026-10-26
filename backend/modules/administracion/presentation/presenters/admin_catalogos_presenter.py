"""
AdminCatalogosPresenter — pure transformer of the filter catalogs.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps a result
object into the typed HTTP wrapper.
"""

from modules.administracion.domain.results.admin_catalogos_results import (
    AdminCatalogosResult,
)
from modules.administracion.presentation.schemas.admin_catalogos_schemas import (
    AdminCatalogoItemOut,
    AdminCatalogoPaqueteOut,
    AdminCatalogosOut,
    AdminEstadosCatalogosOut,
)


class AdminCatalogosPresenter:
    """Transformers of the filter catalogs."""

    @staticmethod
    def present_catalogos(result: AdminCatalogosResult) -> AdminCatalogosOut:
        """Map the catalogs result into its HTTP wrapper."""
        return AdminCatalogosOut(
            evento_id=result.evento_id,
            evento_nombre=result.evento_nombre,
            disciplinas=[
                AdminCatalogoItemOut(
                    id=item.id,
                    nombre=item.nombre,
                    sigla=item.sigla,
                )
                for item in result.disciplinas
            ],
            paquetes=[
                AdminCatalogoPaqueteOut(
                    id=item.id,
                    nombre=item.nombre,
                    tipo=item.tipo,
                )
                for item in result.paquetes
            ],
            promociones=[
                AdminCatalogoItemOut(id=item.id, nombre=item.nombre)
                for item in result.promociones
            ],
            categorias=[
                AdminCatalogoItemOut(id=item.id, nombre=item.nombre)
                for item in result.categorias
            ],
            puntos_acceso=list(result.puntos_acceso),
            estados=AdminEstadosCatalogosOut(
                inscripcion=list(result.estados.inscripcion),
                compra=list(result.estados.compra),
                orden_pago=list(result.estados.orden_pago),
                asignacion_cupo=list(result.estados.asignacion_cupo),
                equipo=list(result.estados.equipo),
                acreditacion=list(result.estados.acreditacion),
                autorizacion_fiesta=list(result.estados.autorizacion_fiesta),
                acceso=list(result.estados.acceso),
                pool=list(result.estados.pool),
                rol_participante=list(result.estados.rol_participante),
            ),
        )


__all__ = ["AdminCatalogosPresenter"]
