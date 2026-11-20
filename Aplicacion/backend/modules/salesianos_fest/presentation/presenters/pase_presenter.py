"""Presenters del CATÁLOGO de pases.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0`
Ledger: `RT-PS-01` (`PaseCatalogoPresenter` → `PaseCatalogoOut`) ·
        `RT-PS-02` (`PaseDetallePresenter` → `PaseDetalleOut`)
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter) ·
          `contract/PLAN_REFACTORIZACION.md` §3.A

Los presenters son TRANSFORMADORES PUROS: reciben un result object y
devuelven un schema HTTP. No consultan la base de datos, no llaman a
selectores y no construyen mensajes públicos de error.
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.pase_result import (
    PaseCatalogoListaResult,
    PaseCatalogoResult,
    PaseDetalleResult,
    PrecioPaseResult,
)
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    PaseCatalogoOut,
    PaseDetalleOut,
    PaseOut,
    PrecioPaseOut,
)


class PaseCatalogoPresenter:
    """Transformador del catálogo de pases."""

    @staticmethod
    def present_catalogo(result: PaseCatalogoListaResult) -> PaseCatalogoOut:
        """Proyecta el catálogo de pases al wrapper HTTP."""
        return PaseCatalogoOut(
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            pases=[
                PaseCatalogoPresenter._present_pase(pase) for pase in result.pases
            ],
        )

    @staticmethod
    def _present_pase(pase: PaseCatalogoResult) -> PaseOut:
        """Proyecta un pase del catálogo."""
        return PaseOut(
            id=UUID(pase.id),
            created_at=pase.created_at,
            updated_at=pase.updated_at,
            edicion_id=UUID(pase.edicion_id),
            edicion_nombre=pase.edicion_nombre,
            nombre=pase.nombre,
            slug=pase.slug,
            descripcion=pase.descripcion,
            estado=pase.estado,
            precio=PaseCatalogoPresenter._present_precio(pase.precio),
        )

    @staticmethod
    def _present_precio(precio: PrecioPaseResult) -> PrecioPaseOut:
        """Proyecta el precio vigente."""
        return PrecioPaseOut(
            monto=precio.monto,
            moneda=precio.moneda,
            vigente_desde=precio.vigente_desde,
            vigente_hasta=precio.vigente_hasta,
        )


class PaseDetallePresenter:
    """Transformador del detalle de un pase."""

    @staticmethod
    def present_detalle(result: PaseDetalleResult) -> PaseDetalleOut:
        """Proyecta el detalle de un pase al wrapper HTTP."""
        return PaseDetalleOut(
            id=UUID(result.id),
            created_at=result.created_at,
            updated_at=result.updated_at,
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            nombre=result.nombre,
            slug=result.slug,
            descripcion=result.descripcion,
            estado=result.estado,
            precio=(
                PaseDetallePresenter._present_precio(result.precio)
                if result.precio is not None
                else None
            ),
        )

    @staticmethod
    def _present_precio(precio: PrecioPaseResult) -> PrecioPaseOut:
        """Proyecta el precio vigente."""
        return PrecioPaseOut(
            monto=precio.monto,
            moneda=precio.moneda,
            vigente_desde=precio.vigente_desde,
            vigente_hasta=precio.vigente_hasta,
        )


__all__ = ["PaseCatalogoPresenter", "PaseDetallePresenter"]
