"""`PagosPresenter` — result de dominio → schema HTTP.

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter) ·
          `contract/PLAN_REFACTORIZACION.md` §3.A

El presenter es un TRANSFORMADOR PURO: recibe un result object y devuelve un
schema HTTP. No consulta la base de datos, no llama a selectores y no
construye mensajes públicos de error.

Reglas:
- un método público por endpoint (`present_confirmado`, `present_orden`);
- sólo `@staticmethod`;
- nada de `z.any()` ni campos genéricos: cada wrapper es tipado;
- la referencia técnica del proveedor **no** se publica: sólo el detalle
  técnico autorizado la expone (FR-04 §1.3).
"""

from modules.pagos.domain.results.pago_result import (
    EstadoActivacionResult,
    EstadoOperativoResult,
    OrdenPagoResult,
    PagoConfirmadoResult,
)
from modules.pagos.presentation.schemas.pago_schemas import (
    EstadoActivacionOut,
    EstadoOperativoOut,
    IntentoPagoOut,
    OrdenPagoOut,
    PagoConfirmadoOut,
)


class PagosPresenter:
    """Transformador del módulo `pagos`."""

    @staticmethod
    def present_estado_operativo(result: EstadoOperativoResult) -> EstadoOperativoOut:
        """Proyecta el veredicto operativo a su wrapper HTTP."""
        return EstadoOperativoOut(
            codigo=result.codigo,
            etiqueta=result.etiqueta,
            descripcion=result.descripcion,
        )

    @staticmethod
    def present_estado_activacion(
        result: EstadoActivacionResult | None,
    ) -> EstadoActivacionOut | None:
        """Proyecta el veredicto de activación a su wrapper HTTP.

        Es un canal SEPARADO del veredicto operativo: el cliente recibe los
        dos hechos sin cruzar por su cuenta los estados hermanos (FR-04 §6).
        """
        if result is None:
            return None
        return EstadoActivacionOut(
            codigo=result.codigo,
            etiqueta=result.etiqueta,
            descripcion=result.descripcion,
            recuperable=result.recuperable,
            proxima_accion=result.proxima_accion,
        )

    @staticmethod
    def present_confirmado(result: PagoConfirmadoResult) -> PagoConfirmadoOut:
        """Proyecta el resultado de una confirmación al wrapper HTTP."""
        return PagoConfirmadoOut(
            orden_pago_id=result.orden_pago_id,
            transaccion_id=result.transaccion_id,
            pagada_en=result.pagada_en,
            referencia=result.referencia,
            estado_orden=result.estado_orden,
            estado_operativo=PagosPresenter.present_estado_operativo(
                result.estado_operativo
            ),
            estado_activacion=PagosPresenter.present_estado_activacion(
                result.estado_activacion
            ),
            ya_confirmado=result.ya_confirmado,
            monto=result.monto,
            moneda=result.moneda,
        )

    @staticmethod
    def present_orden(result: OrdenPagoResult) -> OrdenPagoOut:
        """Proyecta el estado de una orden al wrapper HTTP.

        El historial de intentos viaja en su forma **pública**: sin la
        referencia técnica del proveedor.
        """
        return OrdenPagoOut(
            id=result.id,
            referencia=result.referencia,
            estado=result.estado,
            creada_en=result.creada_en,
            pagada_en=result.pagada_en,
            estado_operativo=PagosPresenter.present_estado_operativo(
                result.estado_operativo
            ),
            estado_activacion=PagosPresenter.present_estado_activacion(
                result.estado_activacion
            ),
            origen_pago=result.origen_pago,
            monto=result.monto,
            moneda=result.moneda,
            intentos=[
                IntentoPagoOut(
                    id=intento.id,
                    intento=intento.intento,
                    estado=intento.estado,
                    verificada=intento.verificada,
                    codigo_respuesta=intento.codigo_respuesta,
                    metodo_pago=intento.metodo_pago,
                    creada_en=intento.creada_en,
                )
                for intento in result.intentos
            ],
        )


class PagoNotificacionPresenter:
    """Presenter de la notificación servidor a servidor (`RT-PG-02`).

    Comparte el wrapper `PagoConfirmadoOut` con la confirmación del navegador
    (ledger FR-07 §3.3): el cliente ve el MISMO veredicto venga la
    confirmación por el canal que venga.
    """

    @staticmethod
    def present_confirmado(result: PagoConfirmadoResult) -> PagoConfirmadoOut:
        """Proyecta el resultado de la notificación al wrapper HTTP."""
        return PagosPresenter.present_confirmado(result)


class OrdenPagoPresenter:
    """Presenter de la lectura del estado de una orden (`RT-PG-03`)."""

    @staticmethod
    def present_orden(result: OrdenPagoResult) -> OrdenPagoOut:
        """Proyecta el estado de la orden al wrapper HTTP."""
        return PagosPresenter.present_orden(result)


__all__ = [
    "OrdenPagoPresenter",
    "PagoNotificacionPresenter",
    "PagosPresenter",
]
