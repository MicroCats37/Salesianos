"""El veredicto operativo: la respuesta única a «¿está pagado esto?».

Freeze: `FREEZE-ENV-1.0.0` (FR-01 §5) · `FREEZE-CM-1.0.0` (FR-04 §1.3)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-01-envelope-error-pagination.md`

`pagos` es el ÚNICO dueño del veredicto. Estos tests comprueban:

1. Que el vocabulario congelado NO se renumera (FR-01 §5.2): son exactamente
   los ocho valores, con los mismos códigos.
2. Que la precedencia es la congelada: una orden pagada nunca se lee como
   cancelada ni vencida.
3. Que el veredicto distingue los cuatro estados de cara al comprador de
   `RN-C07`: pendiente, confirmado, no completado y "estamos verificando".
"""

from datetime import datetime, timedelta, timezone

import pytest

from modules.pagos.domain.constants import (
    DESCRIPCIONES_ESTADO_OPERATIVO,
    EstadoOperativoPago,
    EstadoOrdenPago,
    OrigenPago,
)
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)

pytestmark = pytest.mark.django_db


def _calcular(**kwargs):
    """Atajo del cálculo puro con los hechos por defecto."""
    base = {
        "estado_orden": EstadoOrdenPago.PENDIENTE,
        "compra_pagada": False,
        "compra_cancelada": False,
        "origen_pago": OrigenPago.SIN_PAGO,
        "pagada_en": None,
    }
    base.update(kwargs)
    return EstadoOperativoPagoService.calcular(**base)


# ── El vocabulario congelado ────────────────────────────────────────────────


def test_el_vocabulario_no_se_renumera():
    """El veredicto conserva EXACTAMENTE los ocho valores congelados."""
    assert set(EstadoOperativoPago.values) == {
        "SIN_ORDEN",
        "PAGADA",
        "PAGADA_SIN_LIQUIDAR",
        "PAGADA_SIN_EVIDENCIA",
        "PAGADA_SIN_FECHA",
        "PENDIENTE",
        "CANCELADA",
        "VENCIDA",
    }


def test_cada_veredicto_tiene_etiqueta_y_descripcion():
    """Cada veredicto se publica con etiqueta y descripción (FR-01 §5.1)."""
    for codigo in EstadoOperativoPago.values:
        resultado = EstadoOperativoPagoService.construir_result(codigo)
        assert resultado.codigo == codigo
        assert resultado.etiqueta
        assert resultado.descripcion == DESCRIPCIONES_ESTADO_OPERATIVO[codigo]


def test_la_descripcion_nunca_usa_la_palabra_liquidacion():
    """`RN-C07` / DEC-20: "liquidación" no es lenguaje de cara al operador."""
    for codigo, descripcion in DESCRIPCIONES_ESTADO_OPERATIVO.items():
        assert "liquidaci" not in descripcion.lower(), codigo
        assert "settlement" not in descripcion.lower(), codigo


# ── La precedencia congelada ───────────────────────────────────────────────


def test_sin_orden_no_hay_pago_que_contar():
    """GIVEN una compra sin orden
    WHEN  se calcula el veredicto
    THEN  es SIN_ORDEN.
    """
    assert _calcular(estado_orden=None) == EstadoOperativoPago.SIN_ORDEN


def test_una_orden_pendiente_da_un_pago_pendiente():
    """GIVEN una orden pendiente
    WHEN  se calcula el veredicto
    THEN  es PENDIENTE.
    """
    assert _calcular() == EstadoOperativoPago.PENDIENTE


def test_una_orden_en_verificacion_es_un_pago_pendiente():
    """GIVEN una orden "en verificación"
    WHEN  se calcula el veredicto
    THEN  es PENDIENTE: todavía no hay dinero verificado.
    """
    assert (
        _calcular(estado_orden=EstadoOrdenPago.EN_VERIFICACION)
        == EstadoOperativoPago.PENDIENTE
    )


def test_una_orden_confirmada_sin_compra_pagada_es_pagada_sin_liquidar():
    """GIVEN una orden confirmada pero la compra no consta pagada
    WHEN  se calcula el veredicto
    THEN  es PAGADA_SIN_LIQUIDAR: el dinero entró, el hecho comercial no.
    """
    assert (
        _calcular(
            estado_orden=EstadoOrdenPago.CONFIRMADA,
            compra_pagada=False,
            origen_pago=OrigenPago.IZIPAY,
            pagada_en=datetime.now(timezone.utc),
        )
        == EstadoOperativoPago.PAGADA_SIN_LIQUIDAR
    )


def test_una_orden_confirmada_sin_evidencia_es_pagada_sin_evidencia():
    """GIVEN una orden confirmada, compra pagada y SIN evidencia verificable
    WHEN  se calcula el veredicto
    THEN  es PAGADA_SIN_EVIDENCIA.
    """
    assert (
        _calcular(
            estado_orden=EstadoOrdenPago.CONFIRMADA,
            compra_pagada=True,
            origen_pago=OrigenPago.SIN_PAGO,
            pagada_en=datetime.now(timezone.utc),
        )
        == EstadoOperativoPago.PAGADA_SIN_EVIDENCIA
    )


def test_una_orden_confirmada_sin_fecha_es_pagada_sin_fecha():
    """GIVEN una orden confirmada y evidenciada pero sin fecha de pago
    WHEN  se calcula el veredicto
    THEN  es PAGADA_SIN_FECHA.
    """
    assert (
        _calcular(
            estado_orden=EstadoOrdenPago.CONFIRMADA,
            compra_pagada=True,
            origen_pago=OrigenPago.IZIPAY,
            pagada_en=None,
        )
        == EstadoOperativoPago.PAGADA_SIN_FECHA
    )


def test_una_orden_confirmada_evidenciada_y_fechada_es_pagada():
    """GIVEN una orden confirmada, compra pagada, evidenciada y fechada
    WHEN  se calcula el veredicto
    THEN  es PAGADA.
    """
    assert (
        _calcular(
            estado_orden=EstadoOrdenPago.CONFIRMADA,
            compra_pagada=True,
            origen_pago=OrigenPago.IZIPAY,
            pagada_en=datetime.now(timezone.utc),
        )
        == EstadoOperativoPago.PAGADA
    )


def test_una_orden_pagada_nunca_se_lee_como_cancelada_ni_vencida():
    """Una orden pagada gana siempre: nadie lee que un cobro fue cancelado."""
    codigo = _calcular(
        estado_orden=EstadoOrdenPago.CONFIRMADA,
        compra_pagada=True,
        compra_cancelada=True,
        origen_pago=OrigenPago.IZIPAY,
        pagada_en=datetime.now(timezone.utc),
    )
    assert codigo == EstadoOperativoPago.PAGADA


def test_una_orden_vencida_da_vencida():
    """GIVEN una orden vencida
    WHEN  se calcula el veredicto
    THEN  es VENCIDA.
    """
    assert (
        _calcular(estado_orden=EstadoOrdenPago.VENCIDA)
        == EstadoOperativoPago.VENCIDA
    )


def test_una_orden_fallida_es_un_pago_no_completado():
    """GIVEN una orden cuyo intento falló
    WHEN  se calcula el veredicto
    THEN  es CANCELADA: el "pago no completado" de `RN-C07`.
    """
    assert (
        _calcular(estado_orden=EstadoOrdenPago.FALLIDA)
        == EstadoOperativoPago.CANCELADA
    )


def test_una_compra_cancelada_es_cancelada():
    """GIVEN una compra cancelada
    WHEN  se calcula el veredicto
    THEN  es CANCELADA.
    """
    assert (
        _calcular(compra_cancelada=True) == EstadoOperativoPago.CANCELADA
    )


# ── El veredicto sobre una orden real ─────────────────────────────────────


def test_el_veredicto_de_una_orden_real_usa_los_tres_hechos(
    injector, orden_pago, compra
):
    """GIVEN una orden y su compra
    WHEN  se calcula el veredicto sobre la orden real
    THEN  el veredicto sale del cruce de los TRES hechos, no de uno solo.
    """
    servicio = injector.get(EstadoOperativoPagoService)

    veredicto = servicio.calcular_para_orden(orden_pago)
    assert veredicto.codigo == EstadoOperativoPago.PENDIENTE

    compra.estado = "PAGADA"
    compra.save(update_fields=["estado"])
    orden_pago.estado = EstadoOrdenPago.CONFIRMADA
    orden_pago.pagada_en = datetime.now(timezone.utc) - timedelta(minutes=1)
    orden_pago.save(update_fields=["estado", "pagada_en"])

    veredicto = servicio.calcular_para_orden(orden_pago)
    # Sin evidencia verificable (ningún intento EXITO verificado) el
    # veredicto NO puede ser PAGADA: el pago no está demostrado.
    assert veredicto.codigo == EstadoOperativoPago.PAGADA_SIN_EVIDENCIA
