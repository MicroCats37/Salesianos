"""`CompraPasePresenter` — el resultado de la compra → wrapper HTTP.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`
Ledger: `RT-CM-02` (POST `/pases/compras`) · presenter `CompraPasePresenter`
        · wrapper `CompraPaseCreadaOut` · entrada `ComprarPaseIn` · códigos
        `PASE_NO_DISPONIBLE` (409), `CANTIDAD_INVALIDA` (422).
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

El presenter es un TRANSFORMADOR PURO: no consulta la base de datos y no
construye mensajes públicos de error.

El token de gestión viaja en ESTA respuesta y sólo en esta: es la
credencial del enlace privado y no vuelve a aparecer en ningún listado.
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.pase_result import CompraPaseResultado
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    CompraPaseCreadaOut,
)


class CompraPasePresenter:
    """Transformador de la compra de un lote de pases."""

    @staticmethod
    def present_compra(result: CompraPaseResultado) -> CompraPaseCreadaOut:
        """Proyecta la compra de pases al wrapper HTTP."""
        return CompraPaseCreadaOut(
            compra_pase_id=UUID(result.compra_pase_id),
            compra_id=UUID(result.compra_id),
            orden_pago_id=(
                UUID(result.orden_pago_id) if result.orden_pago_id else None
            ),
            estado=result.estado,
            pase_id=UUID(result.pase_id),
            pase_nombre=result.pase_nombre,
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            cantidad=result.cantidad,
            precio_unitario=result.precio_unitario,
            total=result.total,
            moneda=result.moneda,
            comprador_persona_id=UUID(result.comprador_persona_id),
            comprador_nombres=result.comprador_nombres,
            token=result.token,
            token_expira_en=result.token_expira_en,
            reutilizada=result.reutilizada,
            causa_operativa=result.causa_operativa,
        )


__all__ = ["CompraPasePresenter"]
