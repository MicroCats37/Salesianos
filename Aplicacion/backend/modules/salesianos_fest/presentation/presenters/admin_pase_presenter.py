"""Presenters de la ADMINISTRACIÓN de pases y cortesías.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0`
Ledger: `RT-PS-06` (`AdminPaseListaPresenter` →
        `PaginatedData[AdminPaseListItemOut]`) ·
        `RT-PS-07` (`AdminCortesiaListaPresenter` →
        `PaginatedData[AdminCortesiaListItemOut]`) ·
        `RT-PS-08` (`AdminCortesiaCrearPresenter` → `AdminCortesiaOut`)
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

Los presenters son TRANSFORMADORES PUROS: no consultan la base de datos y no
construyen mensajes públicos de error.

**El token de gestión NO aparece en ningún listado**: es una credencial y
un listado es un sitio donde se filtra.
"""

from uuid import UUID

from core.pagination import PaginatedData
from modules.salesianos_fest.domain.results.pase_result import (
    AdminCortesiaListItemResult,
    AdminCortesiaListaResult,
    AdminPaseListItemResult,
    AdminPaseListaResult,
    CortesiaPaseResult,
)
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    AdminCortesiaListItemOut,
    AdminCortesiaOut,
    AdminPaseListItemOut,
)


class AdminPaseListaPresenter:
    """Transformador del listado administrativo de lotes de pases."""

    @staticmethod
    def present_lista(result: AdminPaseListaResult) -> PaginatedData:
        """Proyecta el listado administrativo de lotes."""
        return PaginatedData[AdminPaseListItemOut](
            items=[
                AdminPaseListaPresenter._present_item(item) for item in result.items
            ],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )

    @staticmethod
    def _present_item(item: AdminPaseListItemResult) -> AdminPaseListItemOut:
        """Proyecta una fila del listado."""
        return AdminPaseListItemOut(
            compra_pase_id=UUID(item.compra_pase_id),
            estado=item.estado,
            pase_id=UUID(item.pase_id),
            pase_nombre=item.pase_nombre,
            edicion_id=UUID(item.edicion_id),
            edicion_nombre=item.edicion_nombre,
            comprador_persona_id=UUID(item.comprador_persona_id),
            comprador_nombres=item.comprador_nombres,
            cantidad=item.cantidad,
            asignados=item.asignados,
            total=item.total,
            moneda=item.moneda,
            creado_en=item.creado_en,
        )


class AdminCortesiaListaPresenter:
    """Transformador del listado administrativo de cortesías."""

    @staticmethod
    def present_lista(result: AdminCortesiaListaResult) -> PaginatedData:
        """Proyecta el listado administrativo de cortesías."""
        return PaginatedData[AdminCortesiaListItemOut](
            items=[
                AdminCortesiaListaPresenter._present_item(item)
                for item in result.items
            ],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )

    @staticmethod
    def _present_item(item: AdminCortesiaListItemResult) -> AdminCortesiaListItemOut:
        """Proyecta una fila del listado."""
        return AdminCortesiaListItemOut(
            id=UUID(item.id),
            pase_nombre=item.pase_nombre,
            edicion_nombre=item.edicion_nombre,
            persona_nombres=item.persona_nombres,
            persona_tipo_documento=item.persona_tipo_documento,
            persona_numero_documento=item.persona_numero_documento,
            estado=item.estado,
            motivo=item.motivo,
            actor_nombres=item.actor_nombres,
            concedido_en=item.concedido_en,
        )


class AdminCortesiaCrearPresenter:
    """Transformador del otorgamiento de una cortesía."""

    @staticmethod
    def present_cortesia(result: CortesiaPaseResult) -> AdminCortesiaOut:
        """Proyecta el acta de cortesía al wrapper HTTP."""
        return AdminCortesiaOut(
            id=UUID(result.id),
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            pase_id=UUID(result.pase_id),
            pase_nombre=result.pase_nombre,
            persona_id=UUID(result.persona_id),
            persona_nombres=result.persona_nombres,
            persona_tipo_documento=result.persona_tipo_documento,
            persona_numero_documento=result.persona_numero_documento,
            estado=result.estado,
            motivo=result.motivo,
            actor_usuario_id=(
                UUID(result.actor_usuario_id) if result.actor_usuario_id else None
            ),
            actor_nombres=result.actor_nombres,
            concedido_en=result.concedido_en,
            revocado_en=result.revocado_en,
        )


__all__ = [
    "AdminCortesiaCrearPresenter",
    "AdminCortesiaListaPresenter",
    "AdminPaseListaPresenter",
]
