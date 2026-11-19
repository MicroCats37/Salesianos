"""Confirmación de un pago: firma, confianza, idempotencia y reintentos.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-1, §3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Estos tests son **de comportamiento**: describen el GIVEN/WHEN/THEN de cada
garantía congelada, no la forma interna del código.

| Test | Garantía congelada |
|---|---|
| `test_la_firma_valida_confirma_la_orden_y_la_compra` | FR-04 §3 — evidencia confiable |
| `test_la_firma_invalida_no_muta_ninguna_fila` | FR-04 §3 — se verifica ANTES de mutar |
| `test_la_notificacion_sin_clave_de_comercio_falla_cerrado` | FR-04 §3 — sin fallback |
| `test_la_notificacion_con_firma_invalida_se_rechaza` | FR-04 §3 |
| `test_un_monto_distinto_de_la_orden_se_rechaza` | FR-04 §3 / `RN-C02` |
| `test_la_confirmacion_repetida_no_duplica_el_pago` | FR-04 I-1 |
| `test_la_notificacion_tardia_no_duplica_el_pago` | FR-04 I-1 |
| `test_el_reenvio_de_otra_persona_se_rechaza` | `TITULARIDAD_COMPRADOR` / `RN-U04` |
| `test_un_pago_sin_firma_verificable_no_confirma_la_orden` | RN-C05 / RN-C07 |
| `test_la_compra_se_marca_pagada_sin_activar_derechos` | RN-C08 / FR-04 §4 |
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra
from modules.pagos.domain.constants import (
    EstadoOperativoPago,
    EstadoOrdenPago,
    EstadoTransaccionPago,
)
from modules.pagos.domain.exceptions import (
    IdempotencyKeyReutilizadaError,
    MontoNoCoincideError,
    PagoFirmaInvalidaError,
    PagoNoAutorizadoError,
    PagoNotificacionNoVerificableError,
)
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.domain.services.flujos.pago_confirmacion_flujo import (
    PagoConfirmacionFlujo,
)
from modules.pagos.tests.fixtures.pagos_fixtures import (
    firmar,
    payload_confirmacion,
    payload_http,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de confirmación, con sus puertos reales."""
    return injector.get(PagoConfirmacionFlujo)


def _confirmar_por_notificacion(flujo, payload, clave):
    """Confirma por el canal servidor a servidor con la firma del payload."""
    crudo = payload_http(payload)
    return async_to_sync(flujo.confirmar_desde_notificacion)(
        payload_http=crudo,
        signature=firmar(crudo, clave),
    )


# ── Evidencia confiable ────────────────────────────────────────────────────


def test_la_firma_valida_confirma_la_orden_y_la_compra(
    flujo, orden_pago, compra, intento, persona, clave_comercio
):
    """GIVEN una notificación firmada correctamente
    WHEN  se confirma el pago
    THEN  la orden queda CONFIRMADA, la compra PAGADA y el veredicto es PAGADA.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    resultado = _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    intento.refresh_from_db()

    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert orden_pago.pagada_en is not None
    assert compra.estado == EstadoCompra.PAGADA
    assert intento.estado == EstadoTransaccionPago.EXITO
    assert intento.verificada is True
    assert resultado.estado_operativo.codigo == EstadoOperativoPago.PAGADA
    assert resultado.ya_confirmado is False


def test_la_firma_invalida_no_muta_ninguna_fila(
    flujo, orden_pago, compra, intento, clave_comercio
):
    """GIVEN una notificación con una firma que NO verifica
    WHEN  se confirma el pago
    THEN  se rechaza con PAGO_FIRMA_INVALIDA y no se muta ninguna fila.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with pytest.raises(PagoFirmaInvalidaError):
        async_to_sync(flujo.confirmar_desde_notificacion)(
            payload_http=crudo,
            signature=firmar(crudo, "otra-clave-distinta"),
        )

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    intento.refresh_from_db()

    assert orden_pago.estado == EstadoOrdenPago.PENDIENTE
    assert orden_pago.pagada_en is None
    assert compra.estado == EstadoCompra.PENDIENTE
    assert intento.estado == EstadoTransaccionPago.PENDIENTE


def test_la_notificacion_sin_clave_de_comercio_falla_cerrado(
    flujo, orden_pago, intento, sin_clave_comercio
):
    """GIVEN un entorno SIN clave del comercio
    WHEN  llega una notificación
    THEN  se rechaza con PAGO_NOTIFICACION_NO_VERIFICABLE: no hay fallback.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with pytest.raises(PagoNotificacionNoVerificableError):
        async_to_sync(flujo.confirmar_desde_notificacion)(
            payload_http=crudo,
            signature=firmar(crudo),
        )

    orden_pago.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.PENDIENTE


def test_la_notificacion_con_firma_invalida_se_rechaza(
    flujo, orden_pago, intento, clave_comercio
):
    """GIVEN una notificación con firma inválida
    WHEN  se confirma
    THEN  se rechaza con PAGO_FIRMA_INVALIDA.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with pytest.raises(PagoFirmaInvalidaError):
        async_to_sync(flujo.confirmar_desde_notificacion)(
            payload_http=crudo,
            signature="firma-que-no-verifica",
        )


def test_un_monto_distinto_de_la_orden_se_rechaza(
    flujo, orden_pago, compra, intento, clave_comercio
):
    """GIVEN una notificación cuyo importe NO es el de la orden
    WHEN  se confirma
    THEN  se rechaza con MONTO_NO_COINCIDE y la orden sigue pendiente.

    El importe de la orden es un snapshot congelado: nadie lo ajusta por el
    camino (`RN-C02`).
    """
    payload = payload_confirmacion(
        transaction_id=intento.referencia_proveedor,
        monto="1.00",
    )

    with pytest.raises(MontoNoCoincideError):
        _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.PENDIENTE
    assert compra.estado == EstadoCompra.PENDIENTE


def test_un_intento_inexistente_se_rechaza(flujo, clave_comercio):
    """GIVEN una notificación de un intento que no existe
    WHEN  se confirma
    THEN  se rechaza con TRANSACCION_PAGO_NO_ENCONTRADA.
    """
    from modules.pagos.domain.exceptions import TransaccionPagoNoEncontradaError

    payload = payload_confirmacion(transaction_id="99999999999999")

    with pytest.raises(TransaccionPagoNoEncontradaError):
        _confirmar_por_notificacion(flujo, payload, clave_comercio)


# ── Idempotencia ────────────────────────────────────────────────────────────


def test_la_confirmacion_repetida_no_duplica_el_pago(
    flujo, orden_pago, compra, intento, clave_comercio
):
    """GIVEN un pago ya confirmado
    WHEN  llega la misma confirmación otra vez
    THEN  el resultado es el mismo y NO hay un segundo hecho de pago.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    primero = _confirmar_por_notificacion(flujo, payload, clave_comercio)
    segundo = _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()

    assert primero.ya_confirmado is False
    assert segundo.ya_confirmado is True
    assert segundo.estado_operativo.codigo == primero.estado_operativo.codigo
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert compra.estado == EstadoCompra.PAGADA

    exitosos = TransaccionPago.objects.filter(
        orden_pago=orden_pago,
        estado=EstadoTransaccionPago.EXITO,
    )
    assert exitosos.count() == 1


def test_la_notificacion_tardia_no_duplica_el_pago(
    flujo, orden_pago, compra, intento, clave_comercio
):
    """GIVEN un pago ya confirmado por otro intento de la misma orden
    WHEN  llega la notificación tardía del intento viejo
    THEN  la orden NO se vuelve a confirmar, su fecha no se reescribe y el
          veredicto sigue siendo el de un pago confirmado.

    El intento tardío **sí** queda registrado (es un hecho del proveedor), pero
    un intento de pago no confirma su orden dos veces (FR-04 I-1).
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    fecha_original = orden_pago.pagada_en

    # Segundo intento de la MISMA orden, que llega tarde.
    intento_tardio = TransaccionPago.objects.create(
        orden_pago=orden_pago,
        intento=2,
        referencia_proveedor="10000000000002",
        estado=EstadoTransaccionPago.PENDIENTE,
    )
    payload_tardio = payload_confirmacion(
        transaction_id=intento_tardio.referencia_proveedor
    )

    resultado = _confirmar_por_notificacion(flujo, payload_tardio, clave_comercio)

    orden_pago.refresh_from_db()
    intento_tardio.refresh_from_db()

    assert resultado.ya_confirmado is True
    assert resultado.estado_operativo.codigo == EstadoOperativoPago.PAGADA
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert orden_pago.pagada_en == fecha_original
    # La traza de auditoría conserva el resultado real del intento tardío.
    assert intento_tardio.estado == EstadoTransaccionPago.EXITO


def test_la_misma_clave_con_otro_payload_es_un_conflicto(
    flujo, orden_pago, compra, intento, persona, clave_comercio
):
    """GIVEN una clave de idempotencia ya usada
    WHEN  llega con un payload DISTINTO
    THEN  se rechaza con IDEMPOTENCY_KEY_REUTILIZADA.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)
    payload_con_firma = {
        **payload,
        "payloadHttp": crudo,
        "signature": firmar(crudo, clave_comercio),
    }

    async_to_sync(flujo.confirmar_desde_navegador)(
        orden_pago_id=str(orden_pago.id),
        payload=payload_con_firma,
        persona_id=str(persona.id),
        ambito_idempotencia="pagos:confirmar:test",
        clave_idempotencia="clave-de-idempotencia-de-prueba",
    )

    otro_payload = payload_confirmacion(
        transaction_id=intento.referencia_proveedor,
        codigo="111",
    )
    crudo_otro = payload_http(otro_payload)

    with pytest.raises(IdempotencyKeyReutilizadaError):
        async_to_sync(flujo.confirmar_desde_navegador)(
            orden_pago_id=str(orden_pago.id),
            payload={
                **otro_payload,
                "payloadHttp": crudo_otro,
                "signature": firmar(crudo_otro, clave_comercio),
            },
            persona_id=str(persona.id),
            ambito_idempotencia="pagos:confirmar:test",
            clave_idempotencia="clave-de-idempotencia-de-prueba",
        )


def test_la_misma_clave_con_el_mismo_payload_devuelve_el_mismo_resultado(
    flujo, orden_pago, compra, intento, persona, clave_comercio
):
    """GIVEN una clave de idempotencia ya usada con el MISMO payload
    WHEN  se repite la operación
    THEN  devuelve el MISMO resultado y no vuelve a cobrar nada.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)
    payload_con_firma = {
        **payload,
        "payloadHttp": crudo,
        "signature": firmar(crudo, clave_comercio),
    }

    primero = async_to_sync(flujo.confirmar_desde_navegador)(
        orden_pago_id=str(orden_pago.id),
        payload=payload_con_firma,
        persona_id=str(persona.id),
        ambito_idempotencia="pagos:confirmar:repetida",
        clave_idempotencia="clave-de-idempotencia-de-prueba",
    )
    segundo = async_to_sync(flujo.confirmar_desde_navegador)(
        orden_pago_id=str(orden_pago.id),
        payload=payload_con_firma,
        persona_id=str(persona.id),
        ambito_idempotencia="pagos:confirmar:repetida",
        clave_idempotencia="clave-de-idempotencia-de-prueba",
    )

    assert primero.orden_pago_id == segundo.orden_pago_id
    assert primero.estado_operativo.codigo == segundo.estado_operativo.codigo
    assert primero.monto == segundo.monto
    assert (
        TransaccionPago.objects.filter(
            orden_pago=orden_pago,
            estado=EstadoTransaccionPago.EXITO,
        ).count()
        == 1
    )


# ── Confianza del canal ─────────────────────────────────────────────────────


def test_el_reenvio_de_otra_persona_se_rechaza(
    flujo, orden_pago, compra, intento, persona, clave_comercio
):
    """GIVEN un reenvío del navegador de una persona que NO es la compradora
    WHEN  se confirma
    THEN  se rechaza con PAGO_NO_AUTORIZADO: el documento NO es credencial.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with pytest.raises(PagoNoAutorizadoError):
        async_to_sync(flujo.confirmar_desde_navegador)(
            orden_pago_id=str(orden_pago.id),
            payload={
                **payload,
                "payloadHttp": crudo,
                "signature": firmar(crudo, clave_comercio),
            },
            persona_id="99999999-9999-9999-9999-999999999999",
        )

    orden_pago.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.PENDIENTE


def test_un_reenvio_sin_actor_se_rechaza(
    flujo, orden_pago, intento, clave_comercio
):
    """GIVEN un reenvío sin actor autenticado
    WHEN  se confirma
    THEN  se rechaza con PAGO_NO_AUTORIZADO.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with pytest.raises(PagoNoAutorizadoError):
        async_to_sync(flujo.confirmar_desde_navegador)(
            orden_pago_id=str(orden_pago.id),
            payload={
                **payload,
                "payloadHttp": crudo,
                "signature": firmar(crudo, clave_comercio),
            },
            persona_id=None,
        )


def test_un_pago_sin_firma_verificable_no_confirma_la_orden(
    flujo, orden_pago, compra, intento, persona, sin_clave_comercio
):
    """GIVEN un reenvío sin firma verificable (no hay clave del comercio)
    WHEN  se confirma
    THEN  la orden NO se confirma: queda en verificación, sin cobrar nada.

    Es el estado "estamos verificando tu pago" de `RN-C07`: nunca se declara
    un pago confirmado sin evidencia confiable (`RN-C05`).
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    resultado = async_to_sync(flujo.confirmar_desde_navegador)(
        orden_pago_id=str(orden_pago.id),
        payload=payload,
        persona_id=str(persona.id),
    )

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    intento.refresh_from_db()

    assert orden_pago.estado == EstadoOrdenPago.EN_VERIFICACION
    assert orden_pago.pagada_en is None
    assert compra.estado == EstadoCompra.PENDIENTE
    assert intento.verificada is False
    assert resultado.estado_operativo.codigo == EstadoOperativoPago.PENDIENTE


# ── Separación pago / derecho ──────────────────────────────────────────────


def test_la_compra_se_marca_pagada_sin_activar_derechos(
    flujo, orden_pago, compra, intento, clave_comercio
):
    """GIVEN un pago verificado
    WHEN  se confirma
    THEN  la compra queda PAGADA pero NO se crea ningún derecho.

    `RN-C08`: el cobro confirmado y la entrega del derecho son hechos
    separados. Este paquete no habilita cupos, entradas ni stock.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    compra.refresh_from_db()
    assert compra.estado == EstadoCompra.PAGADA

    # La garantía congelada NO es "la app de derechos no existe": es que
    # CONFIRMAR EL PAGO NO CONCEDE DERECHOS POR SÍ MISMO (`RN-C08`). Lo que
    # se comprueba es el ESTADO DE LA ACTIVACIÓN, no la presencia del
    # PAQUETE: `modules.salesianos_fest` existe desde DOM-01 (el catálogo de
    # inscripción), pero el ACTIVADOR que concede los derechos del origen
    # `INSCRIPCION` es de DOM-02. Un REGISTRO de activación no es un DERECHO:
    # sin activador, la activación queda PENDIENTE y reintentable, y el pago
    # confirmado se conserva (ver
    # `modules/commerce/tests/integration/test_activacion_compra.py`).
    #
    # Reconciliación A0 de DOM-01 (2026-11-19): la aserción anterior
    # `not apps.is_installed("modules.salesianos_fest")` usaba la AUSENCIA DEL
    # PAQUETE como proxy de la AUSENCIA DE LA CAPACIDAD. DOM-01 creó esa app
    # (que NO posee ninguna tabla de derechos ni ningún activador), así que la
    # premisa quedó obsoleta: era una bomba de relojería. La garantía real es
    # la del ESTADO de la activación, y es la que se comprueba aquí.
    from modules.commerce.domain.constants import EstadoActivacionCompra
    from modules.commerce.domain.models import ActivacionCompra

    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.PENDIENTE
    assert activacion.esta_activada is False
