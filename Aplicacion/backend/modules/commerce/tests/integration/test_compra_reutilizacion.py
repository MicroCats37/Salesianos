"""La reutilización de la compra pendiente: reabrir el checkout no duplica.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-4, I-5; RN-C03, RN-C04)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

| Test | Garantía congelada |
|---|---|
| `test_reabrir_el_checkout_reutiliza_la_compra_pendiente` | I-4 — no se crea otra compra |
| `test_reabrir_el_checkout_no_crea_otra_orden_de_pago` | I-4 — ni otra orden |
| `test_una_compra_ya_pagada_no_se_reutiliza` | I-4 — una compra nueva es una compra nueva |
| `test_cerrar_el_checkout_no_cancela_la_compra` | I-5 — cerrar no es cancelar |
| `test_la_compra_siempre_tiene_un_comprador` | FR-04 §1.1 |
| `test_la_orden_de_pago_replica_el_total_congelado` | FR-04 §1.2 |

Cliente de prueba: el flujo se invoca con `async_to_sync`, el puente correcto
para un flujo async con `sync_to_async(thread_sensitive=True)` (F-12).
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.models import Compra
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo
from modules.pagos.domain.constants import EstadoOrdenPago
from modules.pagos.domain.models import OrdenPago

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de compras."""
    return injector.get(CompraFlujo)


def test_reabrir_el_checkout_reutiliza_la_compra_pendiente(flujo, intencion):
    """GIVEN una compra pendiente de una intención
    WHEN  se pide la compra de la MISMA intención otra vez
    THEN  se reutiliza: hay una sola compra y conserva su identificador.
    """
    primera, reutilizada_1 = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)
    segunda, reutilizada_2 = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    assert reutilizada_1 is False
    assert reutilizada_2 is True
    assert primera.id == segunda.id
    assert Compra.objects.count() == 1


def test_reabrir_el_checkout_no_crea_otra_orden_de_pago(flujo, intencion):
    """GIVEN una compra pendiente con su orden
    WHEN  se pide la compra de la misma intención otra vez
    THEN  se conserva la MISMA orden de pago: no hay cobros duplicados.
    """
    primera, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)
    segunda, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    assert primera.orden_pago_id == segunda.orden_pago_id
    assert OrdenPago.objects.count() == 1


def test_una_compra_ya_pagada_no_se_reutiliza(flujo, intencion):
    """GIVEN una compra ya pagada de una intención
    WHEN  se pide una compra de la misma intención
    THEN  se crea una COMPRA NUEVA: el pago anterior no se reescribe.

    La referencia identifica una **intención pendiente**, no un historial: una
    vez pagada, la misma intención puede abrir otra compra con su propio
    rastro (`RN-M03`).
    """
    primera, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)
    Compra.objects.filter(id=primera.id).update(estado=EstadoCompra.PAGADA)

    segunda, reutilizada = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    assert reutilizada is False
    assert segunda.id != primera.id
    assert Compra.objects.count() == 2
    assert OrdenPago.objects.count() == 2


def test_cerrar_el_checkout_no_cancela_la_compra(flujo, intencion):
    """GIVEN una compra pendiente
    WHEN  el comprador cierra el checkout y vuelve
    THEN  la compra sigue PENDIENTE y es recuperable: cerrar no es cancelar.

    Este paquete no expone ninguna operación de cancelación: `RN-C03` se
    cumple por ausencia de orden de cancelación, no por un estado nuevo.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    assert compra.estado == EstadoCompra.PENDIENTE
    assert compra.orden_pago.estado == EstadoOrdenPago.PENDIENTE

    # Volver a abrir el checkout devuelve la MISMA compra, viva.
    de_nuevo, reutilizada = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)
    assert reutilizada is True
    assert de_nuevo.id == compra.id


def test_la_compra_siempre_tiene_un_comprador(flujo, intencion):
    """GIVEN una intención de compra
    WHEN  se crea la compra
    THEN  la persona compradora es la de la intención y es obligatoria.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    assert compra.persona_id == intencion.persona_id
    assert Compra._meta.get_field("persona").null is False


def test_la_orden_de_pago_replica_el_total_congelado(flujo, intencion):
    """GIVEN una compra creada
    WHEN  se mira su orden de pago
    THEN  el monto y la moneda coinciden EXACTAMENTE con el total congelado.

    `FR-04` §1.2: `OrdenPago.monto`/`moneda` deben coincidir exactamente con
    `Compra.total`/`moneda`.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    orden = compra.orden_pago
    assert orden.monto == compra.total
    assert orden.moneda == compra.moneda
    assert orden.monto == Decimal("100.00")


def test_la_compra_nace_pendiente_y_con_su_origen(flujo, intencion):
    """GIVEN una intención de compra de un dominio
    WHEN  se crea la compra
    THEN  nace PENDIENTE y con el origen del dominio: no hay compra genérica.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    assert compra.estado == EstadoCompra.PENDIENTE
    assert compra.origen == intencion.origen
    assert compra.referencia == intencion.referencia
