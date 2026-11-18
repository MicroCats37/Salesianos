"""
Focused integration tests for the payment attempt lifecycle.

A PENDIENTE TransaccionPago is an ATTEMPT, not a charge: it only records that
a provider session was opened for an order. Every checkout opening creates a
FRESH attempt with a FRESH provider session:

- the live attempt of the order is retired (CANCELADO) and kept as history,
- the new attempt owns its own provider session and its own transaction
  identity — a provider session is NEVER replayed,
- at most one live attempt remains per order,
- the confirmation of a retired or already successful attempt never creates a
  second settlement.
"""
import asyncio
import pytest
from decimal import Decimal

from asgiref.sync import sync_to_async

from modules.pagos.domain.constants import (
    CLAVE_TOKEN_SESION,
    IzipayStatus,
    OrdenPagoStatus,
    SettlementStatus,
)
from modules.pagos.domain.exceptions import (
    IzipayError,
    PagoIntentoEnConflictoError,
)
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
    RegistrarPagoIzipayFlujo,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay
from modules.pagos.tests.fixtures.legacy_data import (
    quitar_guard_de_intento_activo,
    restaurar_guard_de_intento_activo,
)

# The authenticated caller of the browser relay.
PERSONA_PROPIETARIA = "11111111-1111-4111-8111-111111111111"


# ── Doubles ───────────────────────────────────────────────────────────────────

class IzipayClientFake:
    """
    Provider double — records every session it opens.

    `entrada` and `puerta` let a test hold a session open: the provider call
    announces itself through `entrada` and only returns once `puerta` is set.
    That is how an interleaved preparation is reproduced deterministically.
    """

    shop_id = "TEST_SHOP_ID"

    def __init__(
        self,
        nombre: str = "TOKEN",
        entrada: asyncio.Event | None = None,
        puerta: asyncio.Event | None = None,
    ):
        self.nombre = nombre
        self.sesiones = []
        self.entrada = entrada
        self.puerta = puerta

    async def generar_token_sesion(self, **kwargs):
        if self.entrada is not None:
            self.entrada.set()
        if self.puerta is not None:
            await self.puerta.wait()
        self.sesiones.append(kwargs)
        return {"token": f"{self.nombre}-{len(self.sesiones)}"}


class IzipayClientSinToken(IzipayClientFake):
    """Provider double that opens no session at all."""

    async def generar_token_sesion(self, **kwargs):
        self.sesiones.append(kwargs)
        return {}


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


async def _confirmar(flujo, transaction_id: str):
    """Run the confirm step of the flow as the browser relay does."""
    return await flujo._confirmar_pago(
        kr_answer={
            "code": "00",
            "message": "Operación exitosa",
            "transactionId": transaction_id,
        },
        persona_id=PERSONA_PROPIETARIA,
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


async def _obtener(transaction_id: str):
    """Load a transaction by its provider id."""
    return await sync_to_async(TransaccionPago.objects.get)(
        transaction_id=transaction_id
    )


async def _obtener_orden(orden_pago_id: str):
    """Load a payment order."""
    return await sync_to_async(OrdenPago.objects.get)(id=orden_pago_id)


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


# ── Tests: the fresh attempt lifecycle ──────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reabrir_checkout_crea_un_intento_nuevo(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order with a live attempt
    WHEN:  the checkout is reopened
    THEN:  the live attempt is retired and a fresh one is created
    AND    the new transaction identity differs from the previous one
    AND    the provider session of the previous attempt is never replayed
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    primero = await _preparar(flujo, str(orden_pago.id))
    segundo = await _preparar(flujo, str(orden_pago.id))

    assert segundo.transaction_id != primero.transaction_id
    assert segundo.order_number != primero.order_number

    # A provider session is opened per checkout and never handed twice.
    assert len(cliente_falso.sesiones) == 2
    assert segundo.token != primero.token

    # The previous attempt is retired, not deleted: it is the audit trail.
    retirado = await _obtener(primero.transaction_id)
    assert retirado.status == IzipayStatus.CANCELADO

    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1
    assert await _contar(str(orden_pago.id)) == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_el_intento_nuevo_persiste_la_sesion_del_proveedor(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order
    WHEN:  the checkout is prepared
    THEN:  the live attempt persists the provider session it opened
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    resultado = await _preparar(flujo, str(orden_pago.id))

    intento = await _obtener(resultado.transaction_id)
    assert intento.status == IzipayStatus.PENDIENTE
    assert intento.metadata[CLAVE_TOKEN_SESION] == resultado.token
    assert intento.amount == Decimal("100.00")
    assert intento.currency == "PEN"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_los_intentos_superados_se_retiran_todos(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: a pending order with several superseded pending attempts
    WHEN:  the checkout is reopened
    THEN:  every superseded attempt is expired and only one stays pending
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    # The superseded attempts of a legacy deployment only exist with the
    # database guard removed: the guard refuses a second live attempt of the
    # same order.
    await sync_to_async(quitar_guard_de_intento_activo)()
    try:
        for indice in range(3):
            await _crear_intento(
                izipay_core_service, str(orden_pago.id), f"INTENTO-VIEJO-{indice}"
            )
    finally:
        await sync_to_async(restaurar_guard_de_intento_activo)()

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
async def test_preparaciones_concurrentes_dejan_un_solo_intento_vivo(
    izipay_core_service,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: Two preparations of the same pending order that overlap
    WHEN:  the second one supersedes the attempt of the first one
    THEN:  only one live attempt remains
    AND    the superseded caller gets a retryable conflict — never the
           session of a dead attempt
    """
    entrada = asyncio.Event()
    puerta = asyncio.Event()

    cliente_a = IzipayClientFake(nombre="TOKEN-A", entrada=entrada, puerta=puerta)
    cliente_b = IzipayClientFake(nombre="TOKEN-B")

    flujo_a = _flujo(
        izipay_core_service, cliente_a, confirmador_orden_pago, propietario_orden_pago
    )
    flujo_b = _flujo(
        izipay_core_service, cliente_b, confirmador_orden_pago, propietario_orden_pago
    )

    # A opens its provider session and waits there.
    tarea_a = asyncio.create_task(_preparar(flujo_a, str(orden_pago.id)))
    await asyncio.wait_for(entrada.wait(), timeout=5)

    # B supersedes the attempt of A while A is still in the provider.
    resultado_b = await _preparar(flujo_b, str(orden_pago.id))

    # A finishes: its attempt is no longer live, so it gets a conflict.
    puerta.set()
    with pytest.raises(PagoIntentoEnConflictoError):
        await tarea_a

    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 1
    assert await _contar(str(orden_pago.id), IzipayStatus.CANCELADO) == 1

    vivo = await _obtener(resultado_b.transaction_id)
    assert vivo.status == IzipayStatus.PENDIENTE
    assert vivo.metadata[CLAVE_TOKEN_SESION] == resultado_b.token


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_el_intento_se_retira_cuando_el_proveedor_no_devuelve_sesion(
    izipay_core_service,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A provider that opens no session
    WHEN:  the checkout is prepared
    THEN:  the attempt is not a charge and does not stay as the live attempt
    AND    the request is refused
    """
    cliente = IzipayClientSinToken()
    flujo = _flujo(
        izipay_core_service, cliente, confirmador_orden_pago, propietario_orden_pago
    )

    with pytest.raises(IzipayError):
        await _preparar(flujo, str(orden_pago.id))

    assert await _contar(str(orden_pago.id), IzipayStatus.PENDIENTE) == 0
    assert await _contar(str(orden_pago.id), IzipayStatus.FALLIDO) == 1


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


# ── Tests: the collision-safe, order-scoped identity ─────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_la_identidad_de_transaccion_es_unica_por_orden(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order prepared twice and another pending order
    WHEN:  the identities of the attempts are compared
    THEN:  the attempts of the same order share its scope and differ in the
           position they occupy inside it
    AND    the attempts of two different orders never share an identity
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    otro = izipay_core_service.crear_orden_pago(
        numero=izipay_core_service.generar_numero_orden(),
        monto_total=Decimal("100.00"),
        moneda="PEN",
    )

    primero = await _preparar(flujo, str(orden_pago.id))
    segundo = await _preparar(flujo, str(orden_pago.id))
    tercero = await _preparar(flujo, str(otro.id))

    assert len(primero.transaction_id) == 14
    assert primero.transaction_id.isdigit()

    # Same order → same scope (the first six digits).
    assert primero.transaction_id[:6] == segundo.transaction_id[:6]
    # Different position inside the order → never the same identity.
    assert primero.transaction_id[6:10] != segundo.transaction_id[6:10]
    assert primero.transaction_id != segundo.transaction_id

    # Different order → different identity.
    assert primero.transaction_id != tercero.transaction_id


# ── Tests: the confirmation of a retired / successful attempt ────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_un_intento_retirado_no_genera_un_segundo_asentamiento(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A paid order whose payment arrived on a retired attempt
    WHEN:  the live attempt is confirmed later
    THEN:  the outcome of the live attempt is kept in the audit trail
    AND    the payment evidence of the order is not rewritten
    AND    no second settlement is created
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    # A legacy attempt that the next preparation retires.
    await _crear_intento(
        izipay_core_service, str(orden_pago.id), "INTENTO-RETIRADO"
    )
    vivo = await _preparar(flujo, str(orden_pago.id))
    retirado = await _obtener("INTENTO-RETIRADO")
    assert retirado.status == IzipayStatus.CANCELADO

    # The money arrived on the retired attempt: the order is paid and
    # settled — once.
    resultado = await _confirmar(flujo, "INTENTO-RETIRADO")
    assert resultado.success is True
    assert resultado.status == IzipayStatus.EXITO
    assert resultado.settlement_status == SettlementStatus.SETTLED
    assert len(confirmador_orden_pago.llamadas) == 1

    orden_pagada = await _obtener_orden(str(orden_pago.id))
    assert orden_pagada.estado == OrdenPagoStatus.PAGADA
    pagada_en = orden_pagada.pagada_en

    # The live attempt is confirmed later: it is recorded, but the order is
    # not paid twice.
    resultado_vivo = await _confirmar(flujo, vivo.transaction_id)
    assert resultado_vivo.success is True
    assert resultado_vivo.settlement_status != SettlementStatus.SETTLED

    orden_final = await _obtener_orden(str(orden_pago.id))
    assert orden_final.estado == OrdenPagoStatus.PAGADA
    assert orden_final.pagada_en == pagada_en
    assert len(confirmador_orden_pago.llamadas) == 1

    # The audit trail keeps both payments.
    assert (await _obtener("INTENTO-RETIRADO")).status == IzipayStatus.EXITO
    assert (await _obtener(vivo.transaction_id)).status == IzipayStatus.EXITO


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_un_intento_exitoso_es_idempotente(
    izipay_core_service,
    cliente_falso,
    orden_pago,
    confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: An attempt that was already confirmed as a successful payment
    WHEN:  the same confirmation arrives again
    THEN:  the confirmation is idempotent
    AND    the payment evidence of the order is not rewritten
    AND    the order carries a single successful payment
    """
    flujo = _flujo(
        izipay_core_service, cliente_falso, confirmador_orden_pago, propietario_orden_pago
    )

    vivo = await _preparar(flujo, str(orden_pago.id))

    primero = await _confirmar(flujo, vivo.transaction_id)
    assert primero.success is True
    assert primero.already_confirmed is False

    orden_pagada = await _obtener_orden(str(orden_pago.id))
    assert orden_pagada.estado == OrdenPagoStatus.PAGADA
    pagada_en = orden_pagada.pagada_en

    segundo = await _confirmar(flujo, vivo.transaction_id)
    assert segundo.success is True
    assert segundo.already_confirmed is True

    orden_final = await _obtener_orden(str(orden_pago.id))
    assert orden_final.estado == OrdenPagoStatus.PAGADA
    assert orden_final.pagada_en == pagada_en
    assert await _contar(str(orden_pago.id), IzipayStatus.EXITO) == 1
