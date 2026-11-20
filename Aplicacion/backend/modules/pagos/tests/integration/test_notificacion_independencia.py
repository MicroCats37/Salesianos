"""La notificación al comprador nunca revierte una compra.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3 paso 6, §4; RN-C08)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

`NotificarComprador(compra_id)` es el ÚLTIMO paso de la secuencia congelada
(FR-04 §2.3) y es **opcional y reintentable**. La garantía congelada es una
sola y es fuerte: **el fallo de la notificación NUNCA revierte el pago ni el
derecho** (RN-C08, FR-04 §4).

Estos tests son de comportamiento:

| Test | Garantía congelada |
|---|---|
| `test_el_fallo_de_la_notificacion_no_revierte_el_pago_confirmado` | RN-C08 — el cobro y el derecho se conservan |
| `test_la_notificacion_solo_se_intenta_cuando_el_derecho_esta_habilitado` | §4 — no se afirma un hecho que no ocurrió |
| `test_un_webhook_duplicado_no_genera_dos_notificaciones` | I-1 — una notificación efectiva por orden |
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
from modules.commerce.tests.fixtures.activacion_fakes import (  # noqa: F401
    ActivadorDominioFake,
    registro_activadores,
)
from modules.notificaciones.models import NotificacionEnvio
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


def test_el_fallo_de_la_notificacion_no_revierte_el_pago_confirmado(
    flujo, orden_pago, compra, intento, clave_comercio, activador, monkeypatch
):
    """GIVEN un pago verificado y un notificador que falla
    WHEN  se confirma el pago
    THEN  el cobro QUEDA confirmado y el derecho QUEDA habilitado.
    """
    def _reventar(contexto):
        raise RuntimeError("el proveedor de correo no responde")

    monkeypatch.setattr(
        flujo.notificador_service, "notificar_compra_confirmada", _reventar
    )

    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    intento.refresh_from_db()

    # El pago NO se revierte (RN-C08).
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert orden_pago.pagada_en is not None
    assert compra.estado == EstadoCompra.PAGADA
    assert intento.estado == EstadoTransaccionPago.EXITO
    # Y el derecho tampoco.
    assert activador.llamadas_efectivas == 1


def test_la_notificacion_solo_se_intenta_cuando_el_derecho_esta_habilitado(
    flujo, orden_pago, compra, intento, clave_comercio, activador, monkeypatch
):
    """GIVEN un pago verificado cuyo dominio NO pudo activar el derecho
    WHEN  se confirma el pago
    THEN  no se notifica: avisar afirmaría un hecho que no ocurrió.
    """
    activador.fallar = True
    intentos = []

    def _espiar(contexto):
        intentos.append(contexto)
        return None

    monkeypatch.setattr(
        flujo.notificador_service, "notificar_compra_confirmada", _espiar
    )

    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    assert intentos == []


def test_un_webhook_duplicado_no_genera_dos_notificaciones(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago verificado
    WHEN  llega el MISMO webhook otra vez
    THEN  hay una sola notificación: la duplicada no crea otra.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    _confirmar_por_notificacion(flujo, payload, clave_comercio)
    _confirmar_por_notificacion(flujo, payload, clave_comercio)

    assert NotificacionEnvio.objects.count() == 1


def test_la_confirmacion_publica_el_veredicto_de_activacion(
    flujo, orden_pago, compra, intento, clave_comercio, activador
):
    """GIVEN un pago verificado con su derecho habilitado
    WHEN  se confirma el pago
    THEN  el resultado publica el veredicto de activación en su propio canal.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)

    resultado = _confirmar_por_notificacion(flujo, payload, clave_comercio)

    assert resultado.estado_operativo.codigo == "PAGADA"
    assert resultado.estado_activacion is not None
    assert resultado.estado_activacion.codigo == "ACTIVADA"
    assert resultado.estado_activacion.recuperable is False
