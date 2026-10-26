"""
Focused integration tests for the payment attempt lifecycle.

A PENDIENTE TransaccionPago is an ATTEMPT, not a charge: it only records that
a provider session was opened for an order. Re-opening the checkout must not
pile up attempts, so:

- the active attempt is reused while it is still usable (same provider
  session, same transaction id — no second charge opportunity), and
- the superseded attempts are expired before a new one is created.
"""
import pytest
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.utils import timezone

from modules.pagos.domain.constants import (
    CLAVE_TOKEN_SESION,
    INTENTO_REUTILIZABLE_MINUTOS,
    IzipayStatus,
    OrdenPagoStatus,
)
from modules.pagos.domain.exceptions import IzipayError
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
    RegistrarPagoIzipayFlujo,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay


# ── Doubles ───────────────────────────────────────────────────────────────────

class IzipayClientFake:
    """Provider double — records every session it opens."""

    shop_id = "TEST_SHOP_ID"

    def __init__(self):
        self.sesiones = []

    async def generar_token_sesion(self, **kwargs):
        self.sesiones.append(kwargs)
        return {"token": f"TOKEN-{len(self.sesiones)}"}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def izipay_core_service():
    """IzipayCoreService instance."""
    return IzipayCoreService()


@pytest.fixture
def cliente_falso():
    """Provider double that never leaves the process."""
    return IzipayClientFake()


@pytest.fixture
def orden_pago(izipay_core_service):
    """A PENDIENTE OrdenPago ready to be paid."""
    return izipay_core_service.crear_orden_pago(
        numero=izipay_core_service.generar_numero_orden(),
        monto_total=Decimal("100.00"),
        moneda="PEN",
    )


def _flujo(
    izipay_core_service,
    cliente_falso,
    confirmador_orden_pago,
    propietario_orden_pago,
) -> RegistrarPagoIzipayFlujo:
    """Build the flow with the trust doubles of the pagos test suite."""
    return RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=cliente_falso,
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=propietario_orden_pago,
        verificador_firma=VerificadorFirmaIzipay(key_hash=""),
        verificacion_pago=VerificacionPagoService(),
    )


# ── Helpers (ORM access never runs in the async context directly) ───────────

async def _preparar(flujo, orden_pago_id: str):
    """Run the prepare step of the flow."""
    return await flujo._preparar_pago(
        orden_pago_id=orden_pago_id,
        buyer_email="comprador@example.com",
        buyer_name="Ana",
        buyer_surname="Torres",
    )


async def _crear_intento(
    izipay_core_service,
    orden_pago_id: str,
    transaction_id: str,
    amount: str = "100.00",
    metadata: dict | None = None,
):
    """Persist a pending attempt of the given order."""
    return await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=orden_pago_id,
        transaction_id=transaction_id,
        order_number=f"ORDER-{transaction_id}",
        amount=Decimal(amount),
        currency="PEN",
        metadata=metadata,
    )


async def _envejecer(transaction_id: str, minutos: int):
    """Move a transaction back in time — its provider session is stale."""
    return await sync_to_async(
        TransaccionPago.objects.filter(transaction_id=transaction_id).update
    )(created_at=timezone.now() - timedelta(minutes=minutos))


async def _obtener(transaction_id: str):
    """Load a transaction by its provider id."""
    return await sync_to_async(TransaccionPago.objects.get)(
        transaction_id=transaction_id
    )


async def _contar(orden_pago_id: str, status: str | None = None) -> int:
    """Count the attempts of an order, optionally filtered by status."""

    def _count() -> int:
        queryset = TransaccionPago.objects.filter(orden_pago_id=orden_pago_id)
        if status is not None:
            queryset = queryset.filter(status=status)
        return queryset.count()

    return await sync_to_async(_count)()


async def _marcar_pagada(orden_pago):
    """Move an order to the paid state."""

    def _save() -> None:
        orden_pago.estado = OrdenPagoStatus.PAGADA
        orden_pago.save(update_fields=["estado", "updated_at"])

    await sync_to_async(_save)()


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reabrir_checkout_reutiliza_el_intento_activo(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order with a usable pending attempt
    WHEN:  the checkout is reopened
    THEN:  the same attempt is reused — no additional attempt is created
    AND    no second provider session is opened
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    primero = await _preparar(flujo, str(orden_pago.id))
    segundo = await _preparar(flujo, str(orden_pago.id))

    assert segundo.transaction_id == primero.transaction_id
    assert segundo.order_number == primero.order_number
    assert segundo.token == primero.token

    # The provider was called once: the same session continues.
    assert len(cliente_falso.sesiones) == 1

    assert await _contar(str(orden_pago.id)) == 1
    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reabrir_checkout_expira_el_intento_vencido(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order whose active attempt is too old to be reused
    WHEN:  the checkout is reopened
    THEN:  the stale attempt is expired and a new attempt is created
    AND    exactly one attempt stays pending
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    primero = await _preparar(flujo, str(orden_pago.id))
    await _envejecer(primero.transaction_id, INTENTO_REUTILIZABLE_MINUTOS + 1)

    segundo = await _preparar(flujo, str(orden_pago.id))

    assert segundo.transaction_id != primero.transaction_id
    assert len(cliente_falso.sesiones) == 2

    vencido = await _obtener(primero.transaction_id)
    assert vencido.status == IzipayStatus.CANCELADO

    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reabrir_checkout_expira_el_intento_sin_sesion(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order with a pending attempt that holds no provider session
    WHEN:  the checkout is reopened
    THEN:  the attempt without a session is expired and a new one is created
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    await _crear_intento(
        izipay_core_service, str(orden_pago.id), "INTENTO-SIN-TOKEN"
    )

    resultado = await _preparar(flujo, str(orden_pago.id))

    assert resultado.transaction_id != "INTENTO-SIN-TOKEN"

    sin_sesion = await _obtener("INTENTO-SIN-TOKEN")
    assert sin_sesion.status == IzipayStatus.CANCELADO

    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reabrir_checkout_expira_los_intentos_superados(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order with several superseded pending attempts
    WHEN:  the checkout is reopened
    THEN:  every superseded attempt is expired and only one stays pending
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    for indice in range(3):
        await _crear_intento(
            izipay_core_service, str(orden_pago.id), f"INTENTO-VIEJO-{indice}"
        )

    resultado = await _preparar(flujo, str(orden_pago.id))

    assert await _contar(str(orden_pago.id), IzipayStatus.CANCELADO) == 3
    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1
    assert resultado.transaction_id not in (
        "INTENTO-VIEJO-0",
        "INTENTO-VIEJO-1",
        "INTENTO-VIEJO-2",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_intento_con_monto_distinto_no_se_reutiliza(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order whose active attempt carries a different amount
    WHEN:  the checkout is reopened
    THEN:  the mismatched attempt is not reused — a new one is created
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    await _crear_intento(
        izipay_core_service,
        str(orden_pago.id),
        "INTENTO-OTRO-MONTO",
        amount="50.00",
        metadata={CLAVE_TOKEN_SESION: "TOKEN-OTRO"},
    )

    resultado = await _preparar(flujo, str(orden_pago.id))

    assert resultado.transaction_id != "INTENTO-OTRO-MONTO"
    desfasado = await _obtener("INTENTO-OTRO-MONTO")
    assert desfasado.status == IzipayStatus.CANCELADO


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_orden_pagada_no_crea_otro_intento(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: An order that is already paid
    WHEN:  the checkout is opened again
    THEN:  no new attempt is created
    AND    the request is refused
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    await _marcar_pagada(orden_pago)

    with pytest.raises(IzipayError):
        await _preparar(flujo, str(orden_pago.id))

    assert await _contar(str(orden_pago.id)) == 0
    assert cliente_falso.sesiones == []
