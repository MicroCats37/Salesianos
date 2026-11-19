"""El pago confirmado pide la activación del derecho: una vez, y sin revertir.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-1, I-2, §2.3, §4; RN-C06, RN-C08)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Estos tests son **de comportamiento**: describen el GIVEN/WHEN/THEN de la
continuación de la secuencia congelada §2.3 dentro del flujo de pago.

| Test | Garantía congelada |
|---|---|
| `test_la_confirmacion_del_pago_pide_la_activacion_del_derecho` | §2.3 — `ActivarDominio` va después de `CompraMarcadaPagada` |
| `test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces` | I-2 — una activación efectiva por compra |
| `test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces` | RN-C06 — la llegada tardía no duplica derechos |
| `test_el_fallo_de_la_activacion_no_revierte_el_pago_confirmado` | RN-C08 — el cobro se conserva y la incidencia es recuperable |
| `test_un_pago_no_confirmado_no_pide_la_activacion` | RN-C05 — sin evidencia confiable no hay activación |
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import (
    EstadoActivacionCompra,
    EstadoCompra,
    OrigenCompra,
)
from modules.commerce.domain.models import ActivacionCompra
from modules.commerce.tests.fixtures.activacion_fakes import (  # noqa: F401
    ActivadorDominioFake,
    registro_activadores,
)
from modules.pagos.domain.constants import EstadoOrdenPago, EstadoTransaccionPago
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


@pytest.fixture
def activador(registro_activadores):
    """Un activador de dominio registrado para `INSCRIPCION`."""
    doble = ActivadorDominioFake(origen=OrigenCompra.INSCRIPCION)
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, doble)
    return doble


def _confirmar_por_notificacion(flujo, payload, clave):
    """Confirma por el canal servidor a servidor con la firma del payload."""
    crudo = payload_http(payload)
    return async_to_sync(flujo.confirmar_desde_notificacion)(
        payload_http=crudo,
        signature=firmar(crudo, clave),
    )


# ── La secuencia congelada §2.3 ─────────────────────────────────────────────


def test_la_confirmacion_del_pago_pide_la_activacion_del_derecho(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago verificado y su activador de dominio
    WHEN  se confirma el pago
    THEN  la compra queda PAGADA y el derecho queda habilitado UNA vez.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    compra.refresh_from_db()
    assert compra.estado == EstadoCompra.PAGADA
    assert activador.llamadas_efectivas == 1

    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA
    assert activacion.clave == f"activacion:{OrigenCompra.INSCRIPCION}:{compra.id}"


def test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago ya confirmado
    WHEN  llega el MISMO webhook otra vez
    THEN  el derecho no se habilita dos veces: hay una sola activación.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    _confirmar_por_notificacion(flujo, payload, clave_comercio)
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    assert activador.llamadas_efectivas == 1
    assert len(activador.llamadas) == 1
    assert ActivacionCompra.objects.count() == 1

    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA


def test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago que se confirmó tarde, tras un primer intento fallido
    WHEN  se reintenta la activación
    THEN  converge en una sola activación efectiva.
    """
    activador.fallar = True
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.FALLIDA
    assert activador.llamadas_efectivas == 0

    activador.fallar = False
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    activacion.refresh_from_db()
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA
    assert activador.llamadas_efectivas == 1
    assert len(activador.llamadas) == 2


def test_el_fallo_de_la_activacion_no_revierte_el_pago_confirmado(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago verificado y un dominio que falla al activar
    WHEN  se confirma el pago
    THEN  el cobro QUEDA confirmado, la incidencia es visible y reintentable.
    """
    activador.fallar = True
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    resultado = _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    intento.refresh_from_db()

    # El pago NO se revierte (RN-C08).
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert orden_pago.pagada_en is not None
    assert compra.estado == EstadoCompra.PAGADA
    assert intento.estado == EstadoTransaccionPago.EXITO

    # El veredicto OPERATIVO sigue siendo el del pago: `pagos` no conoce el
    # estado de la activación (es un hecho de `commerce`). Publicarlo es
    # trabajo de XCT-03 / API-03, no de este paquete (ver `D-FND-05-01`).
    assert resultado.estado_operativo.codigo == "PAGADA"

    # La incidencia es visible y reintentable, con su acción segura.
    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.FALLIDA
    assert activacion.incidencia["codigo"] == "ACTIVACION_FALLIDA"
    assert activacion.es_reintentable is True


def test_un_pago_no_confirmado_no_pide_la_activacion(
    flujo, orden_pago, compra, intento, sin_clave_comercio, activador
):
    """GIVEN un pago sin evidencia verificable
    WHEN  se reenvía desde el navegador
    THEN  la orden no se confirma y el derecho NO se pide: nada está cobrado.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    async_to_sync(flujo.confirmar_desde_navegador)(
        orden_pago_id=str(orden_pago.id),
        payload=payload,
        persona_id=str(compra.persona_id),
    )

    assert activador.llamadas == []
    assert ActivacionCompra.objects.count() == 0
