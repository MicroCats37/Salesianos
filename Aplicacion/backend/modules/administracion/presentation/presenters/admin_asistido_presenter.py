"""El presenter de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/api-wrapper-presenter-contract.md` §3 — el presenter
TRANSFORMA y nada más: no consulta la base de datos, no llama selectores y no
traduce errores.

Los importes viajan como texto: el total es el que congeló el dueño de la
compra y el presenter sólo lo representa, sin recalcularlo.
"""

from modules.administracion.domain.results.admin_asistido_results import (
    CompraAsistidaResultado,
    CotizacionPaseClienteResultado,
    ParticipanteAsistidoResultado,
)
from modules.administracion.presentation.schemas.admin_asistido_schemas import (
    CompraAsistidaOut,
    CotizacionPaseClienteOut,
    ParticipanteAsistidoOut,
)


class AdminAsistidoPresenter:
    """Traduce los results de los comandos asistidos a sus schemas HTTP."""

    @staticmethod
    def present_participante(
        resultado: ParticipanteAsistidoResultado,
    ) -> ParticipanteAsistidoOut:
        """La participación dada de alta."""
        return ParticipanteAsistidoOut(
            participacion_id=resultado.participacion_id,
            persona_id=resultado.persona_id,
            nombre=resultado.nombre,
            documento=resultado.documento,
            equipo_id=resultado.equipo_id,
            inscripcion_id=resultado.inscripcion_id,
            rol=resultado.rol,
            estado=resultado.estado,
        )

    @staticmethod
    def present_compra(resultado: CompraAsistidaResultado) -> CompraAsistidaOut:
        """La compra asistida y su veredicto de pago."""
        return CompraAsistidaOut(
            compra_id=resultado.compra_id,
            recurso_id=resultado.recurso_id,
            orden_pago_id=resultado.orden_pago_id,
            tipo=resultado.tipo,
            concepto=resultado.concepto,
            total=str(resultado.total),
            moneda=resultado.moneda,
            estado=resultado.estado,
            estado_pago=resultado.estado_pago,
            comprador_persona_id=resultado.comprador_persona_id,
            comprador_nombre=resultado.comprador_nombre,
            cantidad=resultado.cantidad,
            # El importe declarado se representa como TEXTO o `null`: es
            # evidencia auditada, no un total.
            monto_declarado=(
                str(resultado.monto_declarado)
                if resultado.monto_declarado is not None
                else None
            ),
        )

    @staticmethod
    def present_cotizacion(
        resultado: CotizacionPaseClienteResultado,
    ) -> CotizacionPaseClienteOut:
        """La cotización calculada por el servidor.

        Los importes viajan como TEXTO: el presenter sólo los representa, no
        los recalcula ni los contrasta.
        """
        return CotizacionPaseClienteOut(
            pase_id=resultado.pase_id,
            edicion_id=resultado.edicion_id,
            pase_nombre=resultado.pase_nombre,
            cantidad=resultado.cantidad,
            precio_unitario=str(resultado.precio_unitario),
            total=str(resultado.total),
            moneda=resultado.moneda,
            version=resultado.version,
            estado=resultado.estado,
            validez_hasta=resultado.validez_hasta,
        )


__all__ = ["AdminAsistidoPresenter"]
