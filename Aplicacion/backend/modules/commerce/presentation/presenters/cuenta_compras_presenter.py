"""Pure presentation of commercial purchases for the account area."""

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.results.compra_result import CompraResult
from modules.commerce.presentation.schemas.cuenta_compras_schemas import (
    CompraCuentaOut,
    EstadoCompraCuentaOut,
)


_CONCEPTOS = {
    "INSCRIPCION": "Inscripción al festival",
    "PASE": "Pase de fiesta",
    "MARKETPLACE": "Pedido de tienda",
}

_ESTADOS = {
    EstadoCompra.PENDIENTE: (
        "Pendiente de pago",
        "Aún no confirmamos el pago de esta compra.",
    ),
    EstadoCompra.PAGADA: (
        "Pago confirmado",
        "El pago de esta compra fue confirmado.",
    ),
    EstadoCompra.CANCELADA: (
        "Compra cancelada",
        "Esta compra fue cancelada.",
    ),
}


class CuentaComprasPresenter:
    """Transforms commerce results without querying or deciding ownership."""

    @staticmethod
    def present_listado(resultados: list[CompraResult]) -> list[CompraCuentaOut]:
        return [CuentaComprasPresenter.present(compra) for compra in resultados]

    @staticmethod
    def present(compra: CompraResult) -> CompraCuentaOut:
        etiqueta, descripcion = _ESTADOS.get(
            compra.estado,
            ("Estado de compra no reconocido", "No pudimos clasificar esta compra."),
        )
        return CompraCuentaOut(
            id=compra.id,
            origen=compra.origen,
            concepto=_CONCEPTOS.get(compra.origen, "Compra comercial"),
            monto=str(compra.total),
            moneda=compra.moneda,
            fecha=compra.creada_en.date().isoformat(),
            estado=EstadoCompraCuentaOut(
                codigo=compra.estado,
                etiqueta=etiqueta,
                descripcion=descripcion,
            ),
        )


__all__ = ["CuentaComprasPresenter"]
